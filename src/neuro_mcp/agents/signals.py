"""Neurotransmitter Signal Tracker.

Manages the five brain signals defined in .brain/signals/:
- dopamine: reward/salience (per note)
- serotonin: stability/consistency (per note)
- norepinephrine: alertness/vigilance (system-wide)
- acetylcholine: focus/attention (per query, not persisted)
- gaba: inhibition/noise filter (system-wide, computed)

Signals are persisted to .brain/state/signal-levels.json and
agent actions are logged to .brain/state/agent-log.jsonl.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)


class SignalTracker:
    """Read/write neurotransmitter signal levels for the brain."""

    def __init__(self, brain_root: Path) -> None:
        self.brain_root = brain_root
        self.state_dir = brain_root / ".brain" / "state"
        self.signal_file = self.state_dir / "signal-levels.json"
        self.log_file = self.state_dir / "agent-log.jsonl"
        self._lock = Lock()
        self._state: dict[str, Any] = self._load()

    def _ensure_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Any]:
        """Load signal state from disk."""
        if self.signal_file.exists():
            try:
                return json.loads(self.signal_file.read_text("utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not load signal-levels.json: %s", e)
        return {
            "system": {
                "norepinephrine": 0.1,
                "gaba": 0.3,
            },
            "notes": {},  # relative_path → {dopamine, serotonin}
        }

    def _save(self) -> None:
        """Persist signal state to disk."""
        self._ensure_dir()
        self.signal_file.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── System-wide signals ──────────────────────────────────────────

    def get_norepinephrine(self) -> float:
        return self._state.get("system", {}).get("norepinephrine", 0.1)

    def get_gaba(self) -> float:
        return self._state.get("system", {}).get("gaba", 0.3)

    def adjust_system(self, signal: str, delta: float) -> float:
        """Adjust a system-wide signal by delta, clamped to [0, 1]."""
        with self._lock:
            sys = self._state.setdefault("system", {})
            old = sys.get(signal, 0.1)
            new = max(0.0, min(1.0, old + delta))
            sys[signal] = round(new, 3)
            self._save()
            logger.debug("Signal %s: %.3f → %.3f (delta %.3f)", signal, old, new, delta)
            return new

    def set_system(self, signal: str, value: float) -> None:
        """Set a system-wide signal to an absolute value."""
        with self._lock:
            sys = self._state.setdefault("system", {})
            sys[signal] = round(max(0.0, min(1.0, value)), 3)
            self._save()

    # ── Per-note signals ─────────────────────────────────────────────

    def get_note_signals(self, relative_path: str) -> dict[str, float]:
        """Get dopamine + serotonin for a specific note."""
        return self._state.get("notes", {}).get(relative_path, {
            "dopamine": 0.1,
            "serotonin": 0.0,
        })

    def adjust_note(self, relative_path: str, signal: str, delta: float) -> float:
        """Adjust a per-note signal by delta."""
        with self._lock:
            notes = self._state.setdefault("notes", {})
            note = notes.setdefault(relative_path, {"dopamine": 0.1, "serotonin": 0.0})
            old = note.get(signal, 0.0)
            new = max(0.0, min(1.0, old + delta))
            note[signal] = round(new, 3)
            self._save()
            return new

    def set_note(self, relative_path: str, signal: str, value: float) -> None:
        """Set a per-note signal to an absolute value."""
        with self._lock:
            notes = self._state.setdefault("notes", {})
            note = notes.setdefault(relative_path, {"dopamine": 0.1, "serotonin": 0.0})
            note[signal] = round(max(0.0, min(1.0, value)), 3)
            self._save()

    def remove_note(self, relative_path: str) -> None:
        """Remove signal tracking for a note (after archive/delete)."""
        with self._lock:
            self._state.get("notes", {}).pop(relative_path, None)
            self._save()

    # ── GABA computation (derived, not stored directly) ──────────────

    def compute_gaba(self, total_notes: int, stale_notes: int) -> float:
        """Compute GABA from stale/total ratio and store it."""
        if total_notes == 0:
            gaba = 0.3  # default
        else:
            gaba = 1.0 - (stale_notes / total_notes)
        self.set_system("gaba", gaba)
        return gaba

    # ── Snapshot for status reporting ────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        """Return the full signal state for status display."""
        with self._lock:
            return {
                "system": dict(self._state.get("system", {})),
                "note_count": len(self._state.get("notes", {})),
                "top_dopamine": self._top_notes("dopamine", 5),
                "top_serotonin": self._top_notes("serotonin", 5),
            }

    def _top_notes(self, signal: str, n: int) -> list[dict]:
        notes = self._state.get("notes", {})
        ranked = sorted(
            notes.items(),
            key=lambda kv: kv[1].get(signal, 0),
            reverse=True,
        )[:n]
        return [{"path": k, signal: v.get(signal, 0)} for k, v in ranked]

    # ── Agent action log ─────────────────────────────────────────────

    def log_action(
        self,
        agent: str,
        action: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append an entry to agent-log.jsonl."""
        self._ensure_dir()
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "agent": agent,
            "action": action,
        }
        if details:
            entry["details"] = details
        with self._lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
