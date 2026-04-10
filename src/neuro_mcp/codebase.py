from __future__ import annotations

import json
from pathlib import Path

from .config import Settings
from .models import DocKind, DocumentRecord
from .text_utils import make_snippet, normalize_text, path_is_excluded, stable_id


MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
}


def scan_code_documents(settings: Settings) -> tuple[list[DocumentRecord], dict[str, set[str]]]:
    root = settings.code_root
    documents: list[DocumentRecord] = []
    manifests: dict[str, set[str]] = {}

    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if not path.resolve().is_relative_to(root.resolve()):
            continue
        if path_is_excluded(path, settings.exclude_dirs):
            continue
        if path.name not in MANIFEST_NAMES and path.suffix.lower() not in settings.include_extensions:
            continue

        rel_path = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.name in MANIFEST_NAMES:
            manifests[rel_path] = extract_dependencies(path.name, text)

        lines = text.splitlines() or [text]
        if path.suffix.lower() in {".json", ".toml", ".yml", ".yaml", ".md", ".txt"} or path.name in MANIFEST_NAMES:
            chunks = [(1, len(lines), text)]
        else:
            chunks = []
            chunk_lines = max(20, settings.chunk_lines)
            overlap = max(0, min(chunk_lines - 1, settings.chunk_overlap))
            start = 0
            while start < len(lines):
                end = min(len(lines), start + chunk_lines)
                body = "\n".join(lines[start:end])
                chunks.append((start + 1, end, body))
                if end == len(lines):
                    break
                start = end - overlap

        for line_start, line_end, body in chunks:
            title = rel_path
            doc_id = stable_id("code", rel_path, str(line_start), str(line_end))
            documents.append(
                DocumentRecord(
                    doc_id=doc_id,
                    kind=DocKind.CODE,
                    owner_id=rel_path,
                    path=str(path),
                    uri=f"code://{rel_path}#L{line_start}-L{line_end}",
                    title=title,
                    content=body,
                    snippet=make_snippet(body),
                    line_start=line_start,
                    line_end=line_end,
                    content_hash=stable_id(rel_path, normalize_text(body)),
                    metadata={
                        "relative_path": rel_path,
                        "language": path.suffix.lower().lstrip(".") or path.name,
                        "manifest_dependencies": sorted(manifests.get(rel_path, set())),
                    },
                )
            )

    return documents, manifests


def extract_dependencies(file_name: str, text: str) -> set[str]:
    deps: set[str] = set()
    file_name = file_name.lower()
    if file_name == "package.json":
        try:
            payload = json.loads(text)
            for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                values = payload.get(section) or {}
                if isinstance(values, dict):
                    deps.update(values.keys())
        except json.JSONDecodeError:
            return deps
    elif file_name == "requirements.txt":
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            dep = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0]
            dep = dep.split("[")[0].strip()
            if dep:
                deps.add(dep)
    elif file_name == "pyproject.toml":
        import tomllib
        import re as _re
        _dep_split = _re.compile(r"[><=!~;\[ ]")
        try:
            data = tomllib.loads(text)
        except Exception:
            return deps

        # PEP 517 / pyproject style
        project = data.get("project") or {}
        dep_lists: list = list(project.get("dependencies") or [])
        for extra_deps in (project.get("optional-dependencies") or {}).values():
            if isinstance(extra_deps, list):
                dep_lists.extend(extra_deps)

        # Poetry style
        poetry = (data.get("tool") or {}).get("poetry") or {}
        for section in ("dependencies", "dev-dependencies"):
            section_val = poetry.get(section)
            if isinstance(section_val, dict):
                dep_lists.extend(section_val.keys())

        for raw in dep_lists:
            name = _dep_split.split(str(raw))[0].strip()
            if name and name.lower() not in {"python", ""}:
                deps.add(name)
    elif file_name == "cargo.toml":
        inside = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("[dependencies") or line.startswith("[dev-dependencies"):
                inside = True
                continue
            if inside and line.startswith("["):
                inside = False
            if inside and "=" in line:
                dep = line.split("=")[0].strip()
                if dep:
                    deps.add(dep)
    elif file_name == "go.mod":
        in_require_block = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            # Enter multi-line require block: "require ("
            if line.startswith("require") and "(" in line:
                in_require_block = True
                continue
            # Exit multi-line require block
            if in_require_block and line == ")":
                in_require_block = False
                continue
            # Inside block: each non-comment line is "module/path vX.Y.Z [// indirect]"
            if in_require_block and line and not line.startswith("//"):
                dep = line.split()[0].strip()
                if dep:
                    deps.add(dep)
                continue
            # Single-line require: "require module/path vX.Y.Z"
            if line.startswith("require ") and "(" not in line:
                parts = line.removeprefix("require ").split()
                if parts:
                    deps.add(parts[0].strip())
    return deps
