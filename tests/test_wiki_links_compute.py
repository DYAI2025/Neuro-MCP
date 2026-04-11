"""Test wiki-link candidate computation via pairwise similarity."""
from neuro_mcp.embeddings import TfidfEmbedder
from neuro_mcp.hybrid_embeddings import HybridEmbedder
from neuro_mcp.wiki_links import compute_wiki_link_candidates


class _FakeNote:
    def __init__(self, owner_id: str, path: str, content: str):
        self.owner_id = owner_id
        self.path = path
        self.content = content


def _fit_embedder(notes: list[_FakeNote]) -> HybridEmbedder:
    tfidf = TfidfEmbedder(model_path="/tmp/test_wiki_tfidf.joblib")
    embedder = HybridEmbedder(tfidf_embedder=tfidf, model_name=None)
    embedder.fit([n.content for n in notes])
    return embedder


def test_highly_similar_pair_is_returned():
    notes = [
        _FakeNote("a", "brain/a.md", "Python async and await concurrency patterns"),
        _FakeNote("b", "brain/b.md", "Python async and await concurrency patterns for web apps"),
        _FakeNote("c", "brain/c.md", "Cooking recipes with tomatoes and basil"),
    ]
    embedder = _fit_embedder(notes)
    candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.5)

    pairs = {frozenset((c.source_owner_id, c.target_owner_id)) for c in candidates}
    assert frozenset(("a", "b")) in pairs


def test_dissimilar_pairs_are_excluded():
    notes = [
        _FakeNote("a", "brain/a.md", "Python async concurrency"),
        _FakeNote("b", "brain/b.md", "Italian pasta recipes"),
    ]
    embedder = _fit_embedder(notes)
    candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.5)
    assert candidates == []


def test_no_self_pairs():
    """A note should never be paired with itself."""
    notes = [
        _FakeNote("a", "brain/a.md", "identical content one two three"),
        _FakeNote("b", "brain/b.md", "identical content one two three"),
    ]
    embedder = _fit_embedder(notes)
    candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.5)
    for c in candidates:
        assert c.source_owner_id != c.target_owner_id


def test_no_duplicate_pairs():
    """Pair (a,b) and (b,a) are the same — only one should be returned."""
    notes = [
        _FakeNote("a", "brain/a.md", "Python async concurrency"),
        _FakeNote("b", "brain/b.md", "Python async concurrency"),
        _FakeNote("c", "brain/c.md", "Python async concurrency"),
    ]
    embedder = _fit_embedder(notes)
    candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.5)
    # 3 notes → max 3 unique pairs: (a,b), (a,c), (b,c)
    assert len(candidates) <= 3
    pair_sets = [frozenset((c.source_owner_id, c.target_owner_id)) for c in candidates]
    assert len(pair_sets) == len(set(pair_sets))  # no duplicates


def test_threshold_filters_results():
    notes = [
        _FakeNote("a", "brain/a.md", "Python async concurrency one two three"),
        _FakeNote("b", "brain/b.md", "Python async concurrency one two four"),
        _FakeNote("c", "brain/c.md", "completely unrelated tomato basil cooking"),
    ]
    embedder = _fit_embedder(notes)

    loose = compute_wiki_link_candidates(notes, embedder, threshold=0.1)
    strict = compute_wiki_link_candidates(notes, embedder, threshold=0.99)

    assert len(strict) <= len(loose)


def test_empty_notes_list():
    embedder = _fit_embedder([])
    candidates = compute_wiki_link_candidates([], embedder, threshold=0.5)
    assert candidates == []


def test_single_note_returns_no_pairs():
    notes = [_FakeNote("a", "brain/a.md", "only one note exists")]
    embedder = _fit_embedder(notes)
    candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.5)
    assert candidates == []


def test_candidate_has_source_and_target_paths():
    notes = [
        _FakeNote("a", "brain/alpha.md", "identical text one two three"),
        _FakeNote("b", "brain/beta.md", "identical text one two three"),
    ]
    embedder = _fit_embedder(notes)
    candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.5)
    assert len(candidates) >= 1
    for c in candidates:
        assert c.source_path in ("brain/alpha.md", "brain/beta.md")
        assert c.target_path in ("brain/alpha.md", "brain/beta.md")
        assert 0.0 <= c.similarity <= 1.0


def test_unfitted_embedder_returns_empty_with_debug_log(caplog):
    """When the TF-IDF matrix is not fitted, return [] and log at DEBUG."""
    import logging
    tfidf = TfidfEmbedder(model_path="/tmp/test_wiki_unfitted.joblib")
    embedder = HybridEmbedder(tfidf_embedder=tfidf, model_name=None)
    notes = [
        _FakeNote("a", "brain/a.md", "text one"),
        _FakeNote("b", "brain/b.md", "text two"),
    ]
    with caplog.at_level(logging.DEBUG, logger="neuro_mcp.wiki_links"):
        candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.5)
    assert candidates == []
    assert any("not fitted" in rec.message for rec in caplog.records)


def test_shape_mismatch_returns_empty_with_warning(caplog):
    """When notes count differs from matrix rows, return [] and log at WARNING."""
    import logging
    notes = [
        _FakeNote("a", "brain/a.md", "content alpha"),
        _FakeNote("b", "brain/b.md", "content beta"),
        _FakeNote("c", "brain/c.md", "content gamma"),
    ]
    embedder = _fit_embedder(notes)
    # Pass a shorter notes list than the fitted matrix
    short_notes = notes[:2]
    with caplog.at_level(logging.WARNING, logger="neuro_mcp.wiki_links"):
        candidates = compute_wiki_link_candidates(short_notes, embedder, threshold=0.5)
    assert candidates == []
    assert any("does not match" in rec.message for rec in caplog.records)


def test_candidates_sorted_by_similarity_descending():
    """Candidates returned in order: highest similarity first."""
    notes = [
        _FakeNote("a", "brain/a.md", "python async concurrency patterns"),
        _FakeNote("b", "brain/b.md", "python async concurrency patterns exact"),
        _FakeNote("c", "brain/c.md", "python async concurrency patterns almost"),
        _FakeNote("d", "brain/d.md", "python coroutines"),
    ]
    embedder = _fit_embedder(notes)
    candidates = compute_wiki_link_candidates(notes, embedder, threshold=0.1)
    # If we have multiple candidates, they must be sorted descending by similarity
    if len(candidates) >= 2:
        for earlier, later in zip(candidates, candidates[1:]):
            assert earlier.similarity >= later.similarity
