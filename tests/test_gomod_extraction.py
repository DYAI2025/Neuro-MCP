# tests/test_gomod_extraction.py
"""Test dependency extraction from go.mod files."""
from __future__ import annotations

from neuro_mcp.codebase import extract_dependencies


GO_MOD_SINGLE = """
module github.com/myapp/myapp

go 1.21

require github.com/pkg/errors v0.9.1
require golang.org/x/sync v0.3.0
"""

GO_MOD_BLOCK = """
module github.com/myapp/myapp

go 1.21

require (
\tgithub.com/pkg/errors v0.9.1
\tgolang.org/x/sync v0.3.0
\tgithub.com/stretchr/testify v1.8.4
)
"""

GO_MOD_MIXED = """
module github.com/myapp/myapp

go 1.21

require github.com/single/dep v1.0.0

require (
\tgithub.com/block/dep v2.0.0
\tgithub.com/another/dep v3.0.0
)
"""

GO_MOD_WITH_INDIRECT = """
module github.com/myapp/myapp

go 1.21

require (
\tgithub.com/direct/dep v1.0.0
\tgithub.com/indirect/dep v2.0.0 // indirect
)
"""


def test_gomod_single_line_require():
    deps = extract_dependencies("go.mod", GO_MOD_SINGLE)
    assert "github.com/pkg/errors" in deps
    assert "golang.org/x/sync" in deps


def test_gomod_block_require():
    deps = extract_dependencies("go.mod", GO_MOD_BLOCK)
    assert "github.com/pkg/errors" in deps
    assert "golang.org/x/sync" in deps
    assert "github.com/stretchr/testify" in deps


def test_gomod_mixed_require():
    deps = extract_dependencies("go.mod", GO_MOD_MIXED)
    assert "github.com/single/dep" in deps
    assert "github.com/block/dep" in deps
    assert "github.com/another/dep" in deps


def test_gomod_indirect_deps_included():
    deps = extract_dependencies("go.mod", GO_MOD_WITH_INDIRECT)
    assert "github.com/direct/dep" in deps
    assert "github.com/indirect/dep" in deps


def test_gomod_empty():
    deps = extract_dependencies("go.mod", "module foo\ngo 1.21\n")
    assert isinstance(deps, set)
