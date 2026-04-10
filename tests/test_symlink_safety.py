"""Test that scanning ignores symlinks pointing outside root."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from neuro_mcp.config import Settings
from neuro_mcp.notes import scan_brain_documents
from neuro_mcp.codebase import scan_code_documents


@pytest.fixture
def symlink_env(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    outside = tmp_path / "secret"
    outside.mkdir()
    (outside / "leak.md").write_text("---\ntitle: secret\n---\ntop secret data")

    symlink = brain / "evil_link"
    try:
        symlink.symlink_to(outside)
    except OSError:
        pytest.skip("Cannot create symlinks on this OS")

    settings = Settings(brain_root=brain, code_root=code, data_dir=tmp_path / "data")
    return settings, outside


def test_brain_scan_ignores_symlinked_dirs(symlink_env):
    settings, outside = symlink_env
    documents, notes = scan_brain_documents(settings)
    paths = [d.path for d in documents]
    assert not any("leak" in p for p in paths), f"Symlink leak found in: {paths}"


def test_code_scan_ignores_symlinked_dirs(symlink_env):
    settings, outside = symlink_env
    (outside / "evil.py").write_text("print('hacked')")
    documents, manifests = scan_code_documents(settings)
    paths = [d.path for d in documents]
    assert not any("evil" in p for p in paths), f"Symlink leak found in: {paths}"
