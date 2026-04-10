from __future__ import annotations

import sys
import types
from pathlib import Path

from neuro_mcp.config import Settings
from neuro_mcp.server import create_mcp_app


class _FakeFastMCP:
    def __init__(self, name: str, json_response: bool = True):
        self.name = name
        self.json_response = json_response
        self.tools: dict[str, object] = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator

    def resource(self, _uri: str):
        def decorator(func):
            return func

        return decorator

    def prompt(self):
        def decorator(func):
            return func

        return decorator


def _install_fake_mcp() -> None:
    mcp_module = types.ModuleType("mcp")
    server_module = types.ModuleType("mcp.server")
    server_module.FastMCP = _FakeFastMCP
    mcp_module.server = server_module
    sys.modules["mcp"] = mcp_module
    sys.modules["mcp.server"] = server_module


def _seed_brain_and_code(tmp_path: Path) -> Settings:
    brain = tmp_path / "brain"
    brain.mkdir()
    (brain / "overview.md").write_text(
        "---\n"
        "title: Overview\n"
        "type: architecture-doc\n"
        "decay_class: 90d\n"
        "source_precision: 0.9\n"
        "last_verified: 2026-04-10\n"
        "claimed_dependencies: [react]\n"
        "---\n\n"
        "# Overview\n\n"
        "The frontend uses React and a ring visualization.\n"
    )

    code = tmp_path / "code"
    code.mkdir()
    (code / "package.json").write_text('{"dependencies": {"react": "19.0.0"}}\n')

    return Settings(
        brain_root=brain,
        code_root=code,
        data_dir=tmp_path / "data",
        semantic_model=None,
    )


def test_mcp_registers_expected_tools_and_basic_invocation(tmp_path: Path):
    _install_fake_mcp()
    settings = _seed_brain_and_code(tmp_path)

    app = create_mcp_app(settings)

    expected_tools = {
        "search_brain",
        "search_codebase",
        "reconcile_brain_with_code",
        "brain_get_note",
        "brain_get_related",
        "brain_ingest_note",
        "brain_status",
        "freshness_digest",
        "run_garbage_collection",
        "check_interference",
    }
    assert set(app.tools) == expected_tools
    assert len(app.tools) == len(expected_tools)

    search_result = app.tools["search_brain"]("react", top_k=3)
    assert search_result["query"] == "react"

    code_result = app.tools["search_codebase"]("react", top_k=3)
    assert code_result["query"] == "react"

    reconcile = app.tools["reconcile_brain_with_code"]("Are we using react?", top_k=3)
    assert "source_of_truth" in reconcile

    digest = app.tools["freshness_digest"]()
    assert "summary" in digest

    gc_result = app.tools["run_garbage_collection"](dry_run=True)
    assert gc_result["dry_run"] is True

    note = app.tools["brain_get_note"]("overview.md")
    assert note["found"] is True

    related = app.tools["brain_get_related"]("overview.md", top_k=2)
    assert related["found"] is True

    ingest = app.tools["brain_ingest_note"](
        relative_path="80-inbox/new-note.md",
        title="New Note",
        content="# New Note\n\nThis is a new discovery.",
    )
    assert ingest["status"] == "created"

    status = app.tools["brain_status"]()
    assert "total_notes" in status

    interference = app.tools["check_interference"]()
    assert "candidates" in interference
