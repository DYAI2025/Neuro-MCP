"""Verify Agent — auto-verifies note freshness on file save.

Trigger: existing file modified in the vault.

Two modes:
1. QUICK (on file save): User edited the note → set last_verified = now.
   No LLM call. If the human touched it, it's verified by definition.

2. DEEP (periodic): LLM reads the note + linked sources. Checks whether
   the note's claims still hold. Updates last_verified if consistent,
   marks as labile if contradictions found.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .base import AgentConfig, AgentResult, BaseAgent

if TYPE_CHECKING:
    from ..config import Settings
    from ..service import NeuroMCPService

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)

VERIFY_SYSTEM_PROMPT = """\
You are the Verify Agent for a personal knowledge brain. Your job is to check
whether a note's content is still accurate given the current state of linked
sources and related notes.

You will receive:
1. The note's content (with frontmatter)
2. The content of linked source files (if any)
3. Content of related notes (if any)

Decide:
- "verified" — the note is still accurate. Set last_verified to today.
- "labile" — the note contains claims that conflict with sources. Mark as labile.
- "stale" — the note references things that no longer exist. Mark as stale.

Respond with ONLY a JSON object:
{
  "verdict": "verified|labile|stale",
  "confidence": 0.0-1.0,
  "contradictions": ["list of specific contradictions found, or empty"],
  "reasoning": "one sentence explanation"
}
"""


class VerifyAgent(BaseAgent):
    name = "verify"

    def __init__(
        self,
        settings: Settings,
        agent_config: AgentConfig,
        service: NeuroMCPService | None = None,
    ) -> None:
        super().__init__(settings, agent_config)
        self.service = service

    def run_quick(self, file_path: str | Path) -> AgentResult:
        """Quick verify: user edited the file → update last_verified. No LLM."""
        path = Path(file_path)
        if not path.exists() or path.suffix.lower() not in (".md", ".markdown"):
            return AgentResult(
                agent=self.name, success=True,
                action_taken="skipped_non_markdown",
            )

        content = path.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            return AgentResult(
                agent=self.name, success=True,
                action_taken="skipped_no_frontmatter",
            )

        now_iso = datetime.now(UTC).strftime("%Y-%m-%d")

        # Update last_verified in existing frontmatter
        if "last_verified:" in content:
            updated = re.sub(
                r"last_verified:\s*\S+",
                f"last_verified: {now_iso}",
                content,
                count=1,
            )
        else:
            # Insert last_verified after the opening ---
            updated = content.replace("---\n", f"---\nlast_verified: {now_iso}\n", 1)

        if updated != content:
            path.write_text(updated, encoding="utf-8")
            logger.info("[verify-quick] Updated last_verified for %s", path.name)

        return AgentResult(
            agent=self.name,
            success=True,
            action_taken="quick_verified",
            details={"path": str(path.name), "last_verified": now_iso},
        )

    def run(self, file_path: str | Path, **kwargs) -> AgentResult:
        """Deep verify: LLM checks note against linked sources."""
        path = Path(file_path)
        if not path.exists():
            return AgentResult(
                agent=self.name, success=False,
                action_taken="skipped", error=f"Not found: {path}",
            )

        content = path.read_text(encoding="utf-8", errors="replace")

        # Gather linked source content
        linked_content = self._gather_linked_sources(content)

        # Gather related notes via search
        related_content = ""
        if self.service:
            try:
                # Extract a search query from the title
                title_match = re.search(r'title:\s*"?([^"\n]+)"?', content)
                query = title_match.group(1) if title_match else path.stem
                results = self.service.search_brain(query, top_k=3)
                for r in results:
                    if r.path != str(path):
                        related_content += f"\n--- Related: {r.path} ---\n{r.snippet[:500]}\n"
            except Exception as e:
                logger.warning("[verify] Could not get related notes: %s", e)

        user_prompt = (
            f"## Note to verify:\n{content[:3000]}\n\n"
            f"## Linked sources:\n{linked_content[:3000]}\n\n"
            f"## Related notes:\n{related_content[:2000]}"
        )

        try:
            result = self.llm_json(VERIFY_SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.error("[verify] LLM call failed: %s", e)
            return AgentResult(
                agent=self.name, success=False,
                action_taken="llm_error", error=str(e),
            )

        verdict = result.get("verdict", "verified")
        now_iso = datetime.now(UTC).strftime("%Y-%m-%d")

        if verdict == "verified":
            # Update last_verified
            if "last_verified:" in content:
                updated = re.sub(
                    r"last_verified:\s*\S+",
                    f"last_verified: {now_iso}",
                    content, count=1,
                )
            else:
                updated = content.replace("---\n", f"---\nlast_verified: {now_iso}\n", 1)
            path.write_text(updated, encoding="utf-8")
            action = "deep_verified"
        elif verdict == "labile":
            # Add status: labile to frontmatter
            if "status:" in content:
                updated = re.sub(r"status:\s*\S+", "status: labile", content, count=1)
            else:
                updated = content.replace("---\n", "---\nstatus: labile\n", 1)
            path.write_text(updated, encoding="utf-8")
            action = "marked_labile"
        else:
            action = "marked_stale"

        return AgentResult(
            agent=self.name,
            success=True,
            action_taken=action,
            details={
                "path": str(path.name),
                "verdict": verdict,
                "confidence": result.get("confidence", 0),
                "contradictions": result.get("contradictions", []),
                "reasoning": result.get("reasoning", ""),
            },
        )

    def _gather_linked_sources(self, content: str) -> str:
        """Read content of files referenced in linked_paths frontmatter."""
        linked = []
        match = re.search(r"linked_paths:\s*\n((?:\s+-\s+.+\n)*)", content)
        if not match:
            return ""

        for line in match.group(1).strip().split("\n"):
            rel_path = line.strip().lstrip("- ").strip()
            if not rel_path:
                continue
            # Try code_root first, then brain_root
            for root in [self.settings.code_root, self.settings.brain_root]:
                full = root / rel_path
                if full.exists() and full.is_file():
                    try:
                        text = full.read_text(encoding="utf-8", errors="replace")
                        linked.append(f"--- {rel_path} ---\n{text[:1500]}")
                    except Exception:
                        pass
                    break

        return "\n\n".join(linked)
