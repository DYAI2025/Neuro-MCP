from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


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
    bearer_token: SecretStr | None = None
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
    auto_mark_labile: bool = False
    auto_watch: bool = True
    watch_debounce_seconds: float = 5.0
    enable_stc: bool = True
    enable_auto_reconcile: bool = False

    @model_validator(mode="after")
    def _check_search_weights(self) -> "Settings":
        total = self.semantic_weight + self.lexical_weight + self.freshness_weight + self.precision_weight
        if abs(total - 1.0) > 0.05:
            raise ValueError(f"Search weights must sum to ~1.0, got {total:.2f}")
        return self

    @model_validator(mode="after")
    def _check_hybrid_weights(self) -> "Settings":
        total = self.semantic_model_weight + self.tfidf_model_weight
        if abs(total - 1.0) > 0.05:
            raise ValueError(f"Hybrid embedding weights must sum to ~1.0, got {total:.2f}")
        return self

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
