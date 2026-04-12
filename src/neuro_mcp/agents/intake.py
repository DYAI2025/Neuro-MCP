"""Intake Agent — classifies, enriches, and organises new notes.

Trigger: new file appears in the vault (via file watcher).

The human drops a file anywhere. The agent:
1. Reads the content
2. Asks the LLM: what type is this? which folder? what decay class?
3. Writes YAML frontmatter
4. Moves the file to the correct folder if needed
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .base import AgentConfig, AgentResult, BaseAgent

if TYPE_CHECKING:
    from ..config import Settings

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)

INTAKE_SYSTEM_PROMPT = """\
You are the Intake Agent for a personal knowledge brain. Your job is to classify
a new note that just appeared in the vault.

The vault has these folders and their meanings:

- projekte/ — Active projects (decay: 30d, precision: 0.8)
- ideen/ — Ideas, speculative (decay: 7d, precision: 0.3)
- gedanken/ — Thoughts, reflections (decay: 7d, precision: 0.3)
- dialoge/chats/ — Chat conversations (decay: 14d, precision: 0.5)
- dialoge/email/ — Email conversations (decay: 14d, precision: 0.5)
- dialoge/whatsapp/ — WhatsApp conversations (decay: 14d, precision: 0.5)
- agent-dateien/ — Output from AI agents (decay: 30d, precision: 0.7)
- agile-coaching/ — Agile methodology knowledge (decay: 90d, precision: 0.8)
- berufliches/ — Career and work (decay: 60d, precision: 0.7)
- steuer/ — Tax documents (decay: 90d, precision: 0.9)
- weiterbildung/ — Learning and education (decay: 60d, precision: 0.7)
- beziehung/ — Relationship (decay: 30d, precision: 0.5)
- familie/ — Family (decay: 30d, precision: 0.5)
- geld/ — Finance (decay: 60d, precision: 0.85)
- ai/ — AI research, tools, news (decay: 14d, precision: 0.6)
- philosophie/ — Philosophy, deep thinking (decay: 90d, precision: 0.6)

Respond with ONLY a JSON object:
{
  "type": "<note type matching the folder>",
  "folder": "<target folder path>",
  "decay_class": "<7d|14d|30d|60d|90d|immutable>",
  "source_precision": <0.0-1.0>,
  "title": "<concise title for the note>",
  "tags": ["tag1", "tag2", "tag3"],
  "reasoning": "<one sentence why you classified it this way>"
}
"""


class IntakeAgent(BaseAgent):
    name = "intake"

    def __init__(
        self,
        settings: Settings,
        agent_config: AgentConfig,
        auto_move: bool = True,
    ) -> None:
        super().__init__(settings, agent_config)
        self.auto_move = auto_move

    def run(self, file_path: str | Path, **kwargs) -> AgentResult:
        """Classify and enrich a new note."""
        path = Path(file_path)
        if not path.exists():
            return AgentResult(
                agent=self.name,
                success=False,
                action_taken="skipped",
                error=f"File not found: {path}",
            )

        # Skip non-markdown files
        if path.suffix.lower() not in (".md", ".txt", ".markdown"):
            return AgentResult(
                agent=self.name,
                success=True,
                action_taken="skipped_non_markdown",
                details={"path": str(path), "suffix": path.suffix},
            )

        content = path.read_text(encoding="utf-8", errors="replace")

        # Skip if already has frontmatter with type and decay_class
        if content.startswith("---"):
            fm_end = content.find("---", 3)
            if fm_end > 0:
                fm_block = content[3:fm_end]
                if "type:" in fm_block and "decay_class:" in fm_block:
                    return AgentResult(
                        agent=self.name,
                        success=True,
                        action_taken="skipped_already_enriched",
                        details={"path": str(path)},
                    )

        # Build context for LLM
        relative = _safe_relative(path, self.settings.brain_root)
        user_prompt = (
            f"File path: {relative}\n"
            f"File size: {len(content)} characters\n"
            f"Content (first 2000 chars):\n\n"
            f"{content[:2000]}"
        )

        try:
            classification = self.llm_json(INTAKE_SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.error("[intake] LLM classification failed: %s", e)
            return AgentResult(
                agent=self.name,
                success=False,
                action_taken="llm_error",
                error=str(e),
            )

        # Build frontmatter
        now_iso = datetime.now(UTC).strftime("%Y-%m-%d")
        note_type = classification.get("type", "note")
        decay_class = classification.get("decay_class", "30d")
        precision = classification.get("source_precision", 0.5)
        title = classification.get("title", path.stem)
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

        # Write enriched content
        if content.startswith("---"):
            # Replace existing frontmatter
            fm_end = content.find("---", 3)
            if fm_end > 0:
                body = content[fm_end + 3:].lstrip("\n")
            else:
                body = content
        else:
            body = content

        enriched = frontmatter + body
        path.write_text(enriched, encoding="utf-8")
        logger.info("[intake] Enriched %s → type=%s, decay=%s", relative, note_type, decay_class)

        # Move to correct folder if needed
        moved_to = None
        if self.auto_move and folder:
            target_dir = self.settings.brain_root / folder
            target_path = target_dir / path.name
            if target_path != path and target_dir.exists():
                # Don't overwrite existing files
                if not target_path.exists():
                    shutil.move(str(path), str(target_path))
                    moved_to = str(_safe_relative(target_path, self.settings.brain_root))
                    logger.info("[intake] Moved %s → %s", relative, moved_to)

        return AgentResult(
            agent=self.name,
            success=True,
            action_taken="classified_and_enriched",
            details={
                "path": str(relative),
                "type": note_type,
                "decay_class": decay_class,
                "precision": precision,
                "title": title,
                "tags": tags,
                "moved_to": moved_to,
                "reasoning": classification.get("reasoning", ""),
            },
        )


def _safe_relative(path: Path, root: Path) -> Path:
    """Get relative path, falling back to the path itself if not relative."""
    try:
        return path.relative_to(root)
    except ValueError:
        return path
