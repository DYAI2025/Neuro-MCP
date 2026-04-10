# tests/test_toml_extraction.py
"""Test dependency extraction from pyproject.toml."""
from __future__ import annotations

from neuro_mcp.codebase import extract_dependencies


PYPROJECT_PEP517 = """
[project]
name = "myapp"
dependencies = [
    "pydantic>=2.0",
    "numpy>=1.26,<3",
    "scikit-learn>=1.4",
]

[project.optional-dependencies]
dev = ["pytest>=8", "coverage"]
mcp = ["mcp>=1.26,<2", "uvicorn>=0.30"]
"""

PYPROJECT_POETRY = """
[tool.poetry]
name = "myapp"

[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.7"
numpy = "^1.26"

[tool.poetry.dev-dependencies]
pytest = "^8"
"""


def test_pyproject_pep517_dependencies():
    deps = extract_dependencies("pyproject.toml", PYPROJECT_PEP517)
    assert "pydantic" in deps
    assert "numpy" in deps
    assert "scikit-learn" in deps


def test_pyproject_pep517_optional_dependencies():
    deps = extract_dependencies("pyproject.toml", PYPROJECT_PEP517)
    assert "pytest" in deps
    assert "coverage" in deps
    assert "mcp" in deps
    assert "uvicorn" in deps


def test_pyproject_poetry_dependencies():
    deps = extract_dependencies("pyproject.toml", PYPROJECT_POETRY)
    assert "pydantic" in deps
    assert "numpy" in deps


def test_pyproject_invalid_toml_returns_empty():
    deps = extract_dependencies("pyproject.toml", "this is [not valid toml {{{{")
    assert isinstance(deps, set)


def test_pyproject_empty_returns_empty():
    deps = extract_dependencies("pyproject.toml", "")
    assert deps == set()
