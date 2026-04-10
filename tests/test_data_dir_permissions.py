# tests/test_data_dir_permissions.py
"""Test that service warns when data_dir is world-writable."""
from __future__ import annotations

import logging
import os
import stat
from pathlib import Path

import pytest

from neuro_mcp.config import Settings
from neuro_mcp.service import NeuroMCPService


@pytest.mark.skipif(os.name == "nt", reason="chmod not meaningful on Windows")
def test_service_warns_on_world_writable_data_dir(tmp_path: Path, caplog):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    data = tmp_path / "data"
    data.mkdir()

    # Make data_dir world-writable
    data.chmod(data.stat().st_mode | stat.S_IWOTH)

    settings = Settings(brain_root=brain, code_root=code, data_dir=data)
    with caplog.at_level(logging.WARNING, logger="neuro_mcp.service"):
        NeuroMCPService(settings)

    assert any(
        "world-writable" in r.message.lower() or "data_dir" in r.message.lower()
        for r in caplog.records
    ), f"Expected world-writable warning, got: {[r.message for r in caplog.records]}"

    # Cleanup: restore permissions
    data.chmod(data.stat().st_mode & ~stat.S_IWOTH)
