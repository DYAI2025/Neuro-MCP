from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


DEFAULT_EXTENSIONS = [
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".md",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".php",
    ".cs",
    ".sql",
    ".sh",
    ".env.example",
]


class Settings(BaseModel):
    brain_root: Path
    code_root: Path
    data_dir: Path = Path(".neuro_mcp")
    include_extensions: list[str] = Field(default_factory=lambda: list(DEFAULT_EXTENSIONS))
    exclude_dirs: list[str] = Field(default_factory=lambda: [
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        ".next",
        "__pycache__",
    ])
    chunk_lines: int = 80
    chunk_overlap: int = 20
    search_top_k: int = 5
    similarity_threshold: float = 0.85
    stc_window_hours: int = 48
    phasic_change_threshold: int = 20
    immutable_note_types: list[str] = Field(default_factory=lambda: ["adr"])
    mcp_server_name: str = "NeuroMCP"
    mcp_path: str = "/mcp"
    bind_host: str = "127.0.0.1"
    bind_port: int = 8000
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost", "https://localhost"])
    bearer_token: str | None = None
    external_auth_metadata_url: str | None = None
    precision_weight: float = 0.10
    freshness_weight: float = 0.15
    lexical_weight: float = 0.20
    semantic_weight: float = 0.55
    # Hybrid embedding settings
    semantic_model: str | None = "all-MiniLM-L6-v2"
    semantic_model_weight: float = 0.65
    tfidf_model_weight: float = 0.35
    semantic_cache_dir: str | None = None
    auto_watch: bool = True
    watch_debounce_seconds: float = 5.0

    @field_validator("brain_root", "code_root", "data_dir", mode="before")
    @classmethod
    def _expand(cls, value: Any) -> Path:
        return Path(value).expanduser().resolve()

    @classmethod
    def from_file(cls, path: str | Path) -> "Settings":
        raw = Path(path).read_text(encoding="utf-8")
        if str(path).endswith(".json"):
            payload = json.loads(raw)
        else:
            import yaml
            payload = yaml.safe_load(raw)
        return cls(**payload)
