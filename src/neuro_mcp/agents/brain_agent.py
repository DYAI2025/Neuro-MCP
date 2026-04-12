"""Brain-native agent — reads its instructions from .brain/agents/*.md.

This is the LLM-agnostic runtime that bridges markdown agent definitions
to actual execution. Instead of hardcoded Python logic per agent type,
a single BrainAgent class:

1. Reads its markdown definition (trigger, tools, decision table)
2. Builds a system prompt from the markdown
3. Sends context + instructions to any LLM via LLMProvider
4. Parses the LLM's JSON response
5. Executes the decided actions (write frontmatter, move file, etc.)
6. Updates neurotransmitter signals

Any user can write a new agent by adding a .md file to .brain/agents/.
The Synthesis Agent can evolve the system by writing new definitions.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .llm_providers import LLMProvider, LLMConfig, create_provider
from .signals import SignalTracker

if TYPE_CHECKING:
    pass

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    """Parsed content of a .brain/agents/*.md file."""

    name: str
    trigger: str  # new_file, file_modified, code_change, schedule, manual
    requires_llm: bool = True
    mcp_tools: list[str] = field(default_factory=list)
    priority: str = "normal"
    frequency: str = "on_event"
    markdown_body: str = ""  # The full markdown instructions (the system prompt)

    @classmethod
    def from_file(cls, path: Path) -> AgentDefinition:
        """Parse a .brain/agents/*.md file into an AgentDefinition."""
        text = path.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        fm: dict[str, Any] = {}
        body = text
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                fm_text = text[3:end].strip()
                body = text[end + 3:].strip()
                # Simple YAML parsing (avoid dependency)
                # Two-pass: first collect key-value pairs, then handle
                # multiline list values (lines starting with "  - ")
                lines = fm_text.split("\n")
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if ":" in line and not line.startswith("-"):
                        key, _, val = line.partition(":")
                        key = key.strip()
                        val = val.strip()
                        if val.startswith("[") and val.endswith("]"):
                            # Inline list: [a, b, c]
                            items = val[1:-1].split(",")
                            fm[key] = [x.strip().strip("'\"") for x in items if x.strip()]
                        elif val.lower() in ("true", "false"):
                            fm[key] = val.lower() == "true"
                        elif val == "":
                            # Could be a multiline list — check next lines
                            items = []
                            while i + 1 < len(lines) and lines[i + 1].strip().startswith("- "):
                                i += 1
                                items.append(lines[i].strip()[2:].strip())
                            if items:
                                fm[key] = items
                            else:
                                fm[key] = val
                        else:
                            fm[key] = val
                    i += 1

        return cls(
            name=fm.get("agent", path.stem),
            trigger=fm.get("trigger", "manual"),
            requires_llm=fm.get("requires_llm", True),
            mcp_tools=fm.get("mcp_tools", []),
            priority=fm.get("priority", "normal"),
            frequency=fm.get("frequency", "on_event"),
            markdown_body=body,
        )


@dataclass
class BrainAgentResult:
    """Outcome of a brain agent execution."""

    agent: str
    success: bool
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    signal_changes: dict[str, float] = field(default_factory=dict)


class BrainAgent:
    """Universal agent runtime that executes .brain/agents/*.md definitions.

    This replaces the per-agent-type Python classes (IntakeAgent, VerifyAgent)
    with a single class that reads its behavior from markdown.
    """

    def __init__(
        self,
        definition: AgentDefinition,
        llm: LLMProvider,
        brain_root: Path,
        signals: SignalTracker,
    ) -> None:
        self.definition = definition
        self.llm = llm
        self.brain_root = brain_root
        self.signals = signals

    @property
    def name(self) -> str:
        return self.definition.name

    def run_intake(self, file_path: Path) -> BrainAgentResult:
        """Execute intake: classify + enrich + optionally move a new file."""
        if not file_path.exists():
            return BrainAgentResult(
                agent=self.name, success=False,
                action="skipped", error=f"File not found: {file_path}",
            )

        if file_path.suffix.lower() not in (".md", ".txt", ".markdown"):
            return BrainAgentResult(
                agent=self.name, success=True,
                action="skipped_non_markdown",
            )

        content = file_path.read_text(encoding="utf-8", errors="replace")

        # Skip if already fully enriched
        if content.startswith("---"):
            fm_end = content.find("---", 3)
            if fm_end > 0:
                fm_block = content[3:fm_end]
                if "type:" in fm_block and "decay_class:" in fm_block:
                    return BrainAgentResult(
                        agent=self.name, success=True,
                        action="skipped_already_enriched",
                    )

        # Build LLM prompt from the markdown definition
        system_prompt = (
            "Du bist der Intake Agent für ein persönliches Wissenssystem.\n\n"
            "## Deine Anweisungen\n\n"
            f"{self.definition.markdown_body}\n\n"
            "## Antwort-Format\n\n"
            "Antworte NUR mit einem JSON-Objekt:\n"
            "{\n"
            '  "type": "<note type>",\n'
            '  "folder": "<target folder>",\n'
            '  "decay_class": "<7d|14d|30d|60d|90d|immutable>",\n'
            '  "source_precision": <0.0-1.0>,\n'
            '  "title": "<concise title>",\n'
            '  "tags": ["tag1", "tag2", "tag3"],\n'
            '  "reasoning": "<one sentence>"\n'
            "}"
        )

        relative = _safe_relative(file_path, self.brain_root)
        user_prompt = (
            f"Datei: {relative}\n"
            f"Größe: {len(content)} Zeichen\n\n"
            f"Inhalt (erste 2000 Zeichen):\n\n{content[:2000]}"
        )

        try:
            classification = self.llm.chat_json(system_prompt, user_prompt)
        except Exception as e:
            logger.error("[%s] LLM classification failed: %s", self.name, e)
            return BrainAgentResult(
                agent=self.name, success=False,
                action="llm_error", error=str(e),
            )

        # Build and write frontmatter
        now_iso = datetime.now(UTC).strftime("%Y-%m-%d")
        note_type = classification.get("type", "note")
        decay_class = classification.get("decay_class", "30d")
        precision = classification.get("source_precision", 0.5)
        title = classification.get("title", file_path.stem)
        tags = classification.get("tags", [])
        folder = classification.get("folder", "").strip("/")

        frontmatter = (
            f"---\n"
            f'title: "{title}"\n'
            f"type: {note_type}\n"
            f"decay_class: {decay_class}\n"
            f"last_verified: {now_iso}\n"
            f"source_precision: {precision}\n"
            f"tags: [{', '.join(tags)}]\n"
            f"---\n\n"
        )

        # Strip existing frontmatter if present
        body = content
        if content.startswith("---"):
            fm_end = content.find("---", 3)
            if fm_end > 0:
                body = content[fm_end + 3:].lstrip("\n")

        file_path.write_text(frontmatter + body, encoding="utf-8")

        # Move to correct folder
        moved_to = None
        if folder:
            target_dir = self.brain_root / folder
            target_path = target_dir / file_path.name
            if target_path != file_path and target_dir.exists():
                if not target_path.exists():
                    shutil.move(str(file_path), str(target_path))
                    moved_to = str(_safe_relative(target_path, self.brain_root))

        # Update dopamine signal (+0.1 for successful intake)
        note_rel = moved_to or str(relative)
        self.signals.adjust_note(note_rel, "dopamine", 0.1)
        self.signals.log_action(self.name, "classified", {
            "file": note_rel, "type": note_type, "folder": folder,
        })

        return BrainAgentResult(
            agent=self.name, success=True,
            action="classified_and_enriched",
            details={
                "path": str(relative), "type": note_type,
                "decay_class": decay_class, "title": title,
                "tags": tags, "moved_to": moved_to,
            },
            signal_changes={"dopamine": 0.1},
        )

    def run_verify_quick(self, file_path: Path) -> BrainAgentResult:
        """Quick verify: file was edited → update last_verified. No LLM."""
        if not file_path.exists() or file_path.suffix.lower() not in (".md", ".markdown"):
            return BrainAgentResult(
                agent=self.name, success=True,
                action="skipped_non_markdown",
            )

        content = file_path.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            return BrainAgentResult(
                agent=self.name, success=True,
                action="skipped_no_frontmatter",
            )

        now_iso = datetime.now(UTC).strftime("%Y-%m-%d")

        if "last_verified:" in content:
            updated = re.sub(
                r"last_verified:\s*\S+",
                f"last_verified: {now_iso}",
                content, count=1,
            )
        else:
            updated = content.replace("---\n", f"---\nlast_verified: {now_iso}\n", 1)

        if updated != content:
            file_path.write_text(updated, encoding="utf-8")

        # Update serotonin (+0.1 for verification)
        relative = str(_safe_relative(file_path, self.brain_root))
        self.signals.adjust_note(relative, "serotonin", 0.1)
        self.signals.log_action(self.name, "quick_verified", {"file": relative})

        return BrainAgentResult(
            agent=self.name, success=True,
            action="quick_verified",
            details={"path": file_path.name, "last_verified": now_iso},
            signal_changes={"serotonin": 0.1},
        )

    def run_verify_deep(self, file_path: Path, related_content: str = "") -> BrainAgentResult:
        """Deep verify: LLM checks note against sources."""
        if not file_path.exists():
            return BrainAgentResult(
                agent=self.name, success=False,
                action="skipped", error=f"Not found: {file_path}",
            )

        content = file_path.read_text(encoding="utf-8", errors="replace")

        system_prompt = (
            "Du bist der Verify Agent für ein persönliches Wissenssystem.\n\n"
            "## Deine Anweisungen\n\n"
            f"{self.definition.markdown_body}\n\n"
            "## Antwort-Format\n\n"
            "Antworte NUR mit einem JSON-Objekt:\n"
            "{\n"
            '  "verdict": "verified|labile|stale",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "contradictions": ["list or empty"],\n'
            '  "reasoning": "one sentence"\n'
            "}"
        )

        user_prompt = (
            f"## Notiz:\n{content[:3000]}\n\n"
            f"## Verwandte Notizen:\n{related_content[:2000]}"
        )

        try:
            result = self.llm.chat_json(system_prompt, user_prompt)
        except Exception as e:
            return BrainAgentResult(
                agent=self.name, success=False,
                action="llm_error", error=str(e),
            )

        verdict = result.get("verdict", "verified")
        now_iso = datetime.now(UTC).strftime("%Y-%m-%d")
        relative = str(_safe_relative(file_path, self.brain_root))

        if verdict == "verified":
            if "last_verified:" in content:
                updated = re.sub(r"last_verified:\s*\S+", f"last_verified: {now_iso}", content, count=1)
            else:
                updated = content.replace("---\n", f"---\nlast_verified: {now_iso}\n", 1)
            file_path.write_text(updated, encoding="utf-8")
            self.signals.adjust_note(relative, "serotonin", 0.1)
            action = "deep_verified"
        elif verdict == "labile":
            if "status:" in content:
                updated = re.sub(r"status:\s*\S+", "status: labile", content, count=1)
            else:
                updated = content.replace("---\n", "---\nstatus: labile\n", 1)
            file_path.write_text(updated, encoding="utf-8")
            self.signals.adjust_note(relative, "serotonin", -0.2)
            action = "marked_labile"
        else:
            self.signals.adjust_note(relative, "serotonin", -0.3)
            action = "marked_stale"

        self.signals.log_action(self.name, action, {
            "file": relative, "verdict": verdict,
            "contradictions": result.get("contradictions", []),
        })

        return BrainAgentResult(
            agent=self.name, success=True,
            action=action,
            details={
                "path": relative, "verdict": verdict,
                "confidence": result.get("confidence", 0),
                "contradictions": result.get("contradictions", []),
            },
        )

    def run_gc(
        self,
        stale_notes: list[dict[str, Any]],
        total_notes: int,
    ) -> BrainAgentResult:
        """GC Agent: review stale notes and decide archive candidates.

        Does NOT delete — returns candidates. Respects serotonin protection.
        """
        # Filter out notes with high serotonin (protected)
        candidates = []
        for note in stale_notes:
            path = note.get("path", "")
            signals = self.signals.get_note_signals(path)
            if signals.get("serotonin", 0) > 0.7:
                logger.debug("[gc] Skipping protected note: %s (serotonin=%.2f)",
                             path, signals["serotonin"])
                continue
            if signals.get("dopamine", 0) > 0.5:
                logger.debug("[gc] Skipping active note: %s (dopamine=%.2f)",
                             path, signals["dopamine"])
                continue
            candidates.append(note)

        # Update GABA
        gaba = self.signals.compute_gaba(total_notes, len(stale_notes))

        self.signals.log_action(self.name, "gc_sweep", {
            "total_notes": total_notes,
            "stale_notes": len(stale_notes),
            "candidates_after_filter": len(candidates),
            "gaba": gaba,
        })

        return BrainAgentResult(
            agent=self.name, success=True,
            action="gc_sweep",
            details={
                "candidates": [c.get("path") for c in candidates],
                "filtered_count": len(stale_notes) - len(candidates),
                "gaba": gaba,
            },
            signal_changes={"gaba": gaba},
        )

    def run_reconcile(self, topic: str, brain_results: list, code_results: list) -> BrainAgentResult:
        """Reconcile Agent: check brain notes against code truth.

        Uses LLM to find contradictions between brain claims and code state.
        """
        system_prompt = (
            "Du bist der Reconcile Agent für ein Wissenssystem.\n\n"
            "## Deine Anweisungen\n\n"
            f"{self.definition.markdown_body}\n\n"
            "## Antwort-Format\n\n"
            "Antworte NUR mit einem JSON-Objekt:\n"
            "{\n"
            '  "contradictions": [{"brain_note": "...", "code_file": "...", "issue": "..."}],\n'
            '  "action_taken": "reconciled|no_contradictions|needs_review",\n'
            '  "norepinephrine_delta": 0.0\n'
            "}"
        )

        brain_text = "\n".join(
            f"- {r.path}: {r.snippet[:200]}" for r in brain_results[:5]
        ) if brain_results else "(keine Brain-Ergebnisse)"
        code_text = "\n".join(
            f"- {r.path}: {r.snippet[:200]}" for r in code_results[:5]
        ) if code_results else "(keine Code-Ergebnisse)"

        user_prompt = (
            f"Thema: {topic}\n\n"
            f"## Brain-Notizen:\n{brain_text}\n\n"
            f"## Code-Zustand:\n{code_text}"
        )

        try:
            result = self.llm.chat_json(system_prompt, user_prompt)
        except Exception as e:
            return BrainAgentResult(
                agent=self.name, success=False,
                action="llm_error", error=str(e),
            )

        contradictions = result.get("contradictions", [])
        ne_delta = result.get("norepinephrine_delta", 0.0)

        if contradictions:
            self.signals.adjust_system("norepinephrine", 0.3)

        self.signals.log_action(self.name, "reconcile", {
            "topic": topic,
            "contradiction_count": len(contradictions),
        })

        return BrainAgentResult(
            agent=self.name, success=True,
            action=result.get("action_taken", "reconciled"),
            details={
                "topic": topic,
                "contradictions": contradictions,
            },
        )


# ── Helpers ──────────────────────────────────────────────────────────

def _safe_relative(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def load_agent_definitions(brain_root: Path) -> dict[str, AgentDefinition]:
    """Load all .brain/agents/*.md files into AgentDefinitions."""
    agents_dir = brain_root / ".brain" / "agents"
    if not agents_dir.exists():
        logger.info("No .brain/agents/ directory found at %s", agents_dir)
        return {}

    definitions: dict[str, AgentDefinition] = {}
    for md_file in sorted(agents_dir.glob("*.md")):
        try:
            defn = AgentDefinition.from_file(md_file)
            definitions[defn.name] = defn
            logger.debug("Loaded agent definition: %s (trigger=%s)", defn.name, defn.trigger)
        except Exception as e:
            logger.warning("Failed to load agent definition %s: %s", md_file.name, e)

    logger.info("Loaded %d agent definitions from %s", len(definitions), agents_dir)
    return definitions
