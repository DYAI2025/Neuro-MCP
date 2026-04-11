from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

DecayClass = Literal["immutable", "90d", "60d", "30d", "14d", "7d"]


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


class FolderTypeRule(BaseModel):
    type: str
    decay_class: DecayClass = "30d"


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
    # For interference detection (check_interference): near-duplicate flagging
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
    enable_auto_enrich_frontmatter: bool = False
    enable_auto_wiki_links: bool = False
    folder_type_map: dict[str, FolderTypeRule] = Field(default_factory=dict)
    # For wiki-link generation (auto_wiki_links): lower = more links.
    # 0.8 is stricter than the TF-IDF literature default (~0.7) — we prefer
    # fewer but more confident links. Must stay below similarity_threshold (0.85)
    # so wiki-links activate before interference/near-duplicate flagging.
    auto_link_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

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

    def resolve_folder_type(self, relative_path: str | Path) -> FolderTypeRule | None:
        """Find the FolderTypeRule whose prefix matches `relative_path`.

        Matches by longest-prefix-wins. Path separators are normalized so
        the same map works on POSIX and Windows. Returns None if no rule matches.
        """
        if not self.folder_type_map:
            return None
        normalized = str(relative_path).replace("\\", "/")
        matches = [
            (prefix, rule)
            for prefix, rule in self.folder_type_map.items()
            if normalized.startswith(prefix.rstrip("/") + "/") or normalized == prefix
        ]
        if not matches:
            return None
        matches.sort(key=lambda pair: len(pair[0]), reverse=True)
        return matches[0][1]

    @classmethod
    def from_file(cls, path: str | Path) -> "Settings":
        raw = Path(path).read_text(encoding="utf-8")
        if str(path).endswith(".json"):
            payload = json.loads(raw)
        else:
            import yaml
            payload = yaml.safe_load(raw)
        return cls(**payload)
