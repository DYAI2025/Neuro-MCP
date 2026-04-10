from __future__ import annotations

import subprocess
from pathlib import Path

from .models import ChangeSet, Mode


def _run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def current_head(repo_root: str | Path) -> str | None:
    repo_root = Path(repo_root)
    value = _run_git(repo_root, "rev-parse", "HEAD")
    return value or None


def recent_commit_subjects(repo_root: str | Path, limit: int = 10) -> list[str]:
    repo_root = Path(repo_root)
    output = _run_git(repo_root, "log", f"-n{limit}", "--pretty=format:%h %s")
    return [line for line in output.splitlines() if line.strip()]


def changed_files_since(repo_root: str | Path, base_ref: str | None = None) -> list[str]:
    repo_root = Path(repo_root)
    if not base_ref:
        base_ref = "HEAD~1"
    output = _run_git(repo_root, "diff", "--name-only", base_ref, "HEAD")
    return [line for line in output.splitlines() if line.strip()]


def detect_mode(repo_root: str | Path, threshold: int = 20) -> ChangeSet:
    repo_root = Path(repo_root)
    changed = changed_files_since(repo_root)
    mode = Mode.TONIC if len(changed) >= threshold else Mode.PHASIC
    return ChangeSet(
        changed_paths=changed,
        recent_commits=recent_commit_subjects(repo_root, limit=10),
        mode=mode,
    )
