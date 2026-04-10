from __future__ import annotations

from pathlib import Path

from neuro_mcp.config import Settings


def test_settings_has_semantic_fields():
    s = Settings(brain_root="/tmp/brain", code_root="/tmp/code")
    assert hasattr(s, "semantic_model")
    assert hasattr(s, "semantic_model_weight")
    assert hasattr(s, "tfidf_model_weight")
    assert s.semantic_model == "all-MiniLM-L6-v2"
    assert s.semantic_model_weight == 0.65
    assert s.tfidf_model_weight == 0.35


def test_service_uses_hybrid_embedder(tmp_path: Path):
    brain = tmp_path / "brain"
    brain.mkdir()
    code = tmp_path / "code"
    code.mkdir()
    s = Settings(brain_root=str(brain), code_root=str(code), data_dir=str(tmp_path / "data"), semantic_model=None)
    from neuro_mcp.service import NeuroMCPService
    svc = NeuroMCPService(s)
    from neuro_mcp.hybrid_embeddings import HybridEmbedder
    assert isinstance(svc.brain_hybrid, HybridEmbedder)
    assert isinstance(svc.code_hybrid, HybridEmbedder)
