from __future__ import annotations

import numpy as np

from neuro_mcp.interference import check_interference


def test_check_interference_finds_similar_pair():
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.98, 0.1, 0.0],
        [0.0, 0.0, 1.0],
    ])
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    paths = ["note-a.md", "note-b.md", "note-c.md"]
    owner_ids = ["owner-a", "owner-b", "owner-c"]

    candidates = check_interference(embeddings, paths, owner_ids, threshold=0.85)
    assert len(candidates) == 1
    assert candidates[0].note_a_path == "note-a.md"
    assert candidates[0].note_b_path == "note-b.md"
    assert candidates[0].similarity >= 0.85


def test_check_interference_same_owner_is_merge():
    embeddings = np.array([
        [1.0, 0.0],
        [0.99, 0.05],
    ])
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    candidates = check_interference(
        embeddings,
        paths=["a/sec1.md", "a/sec2.md"],
        owner_ids=["owner-a", "owner-a"],
        threshold=0.85,
    )
    assert len(candidates) == 1
    assert candidates[0].action == "merge"


def test_check_interference_different_owner_is_crosslink():
    embeddings = np.array([
        [1.0, 0.0],
        [0.99, 0.05],
    ])
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    candidates = check_interference(
        embeddings,
        paths=["a.md", "b.md"],
        owner_ids=["owner-a", "owner-b"],
        threshold=0.85,
    )
    assert len(candidates) == 1
    assert candidates[0].action == "cross_link"


def test_check_interference_no_matches_below_threshold():
    embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
    ])
    candidates = check_interference(
        embeddings, ["a.md", "b.md"], ["o-a", "o-b"], threshold=0.85,
    )
    assert len(candidates) == 0


def test_check_interference_empty():
    embeddings = np.zeros((1, 3))
    candidates = check_interference(embeddings, ["a.md"], ["o-a"], threshold=0.85)
    assert len(candidates) == 0
