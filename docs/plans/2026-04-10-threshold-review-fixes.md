# Threshold Config Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address L-1, L-2, S-2, S-3 review findings on the `auto_link_threshold` config: add inline documentation for both similarity thresholds, raise the default to 0.8 for stricter "identical enough to link" semantics, use Pydantic's `ValidationError` specifically in tests, and expand boundary/near-boundary test coverage.

**Architecture:** Purely config-layer changes. No runtime impact beyond the default value change (nothing consumes `auto_link_threshold` yet — it's only set up for the upcoming wiki-links compute task).

**Tech Stack:** Python 3.11+, Pydantic 2, pytest

---

### Task 1: Add inline comments to both similarity thresholds (L-1 + L-2)

**Files:**
- Modify: `src/neuro_mcp/config.py:54` (`similarity_threshold`)
- Modify: `src/neuro_mcp/config.py:85` (`auto_link_threshold`)

**Step 1: Add comments above each threshold field**

Find `similarity_threshold: float = 0.85` and replace with:

```python
    # For interference detection (check_interference): near-duplicate flagging
    similarity_threshold: float = 0.85
```

Find `auto_link_threshold: float = Field(default=0.7, ge=0.0, le=1.0)` and replace with:

```python
    # For wiki-link generation (auto_wiki_links): lower = more links.
    # 0.8 is stricter than the TF-IDF literature default (~0.7) — we prefer
    # fewer but more confident links. Must stay below similarity_threshold (0.85)
    # so wiki-links activate before interference/near-duplicate flagging.
    auto_link_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
```

**Step 2: Run existing tests — expect 1 failure**

```bash
uv run pytest tests/test_auto_link_threshold.py::test_auto_link_threshold_defaults_to_0_7 -v
```
Expected: FAIL — default is now 0.8.

**Step 3: Do NOT commit yet** — continue to Task 2.

---

### Task 2: Rename and update the default-value test (part of L-1 fix)

**Files:**
- Modify: `tests/test_auto_link_threshold.py`

**Step 1: Rename the test and update the assertion**

Find:

```python
def test_auto_link_threshold_defaults_to_0_7():
    s = _settings()
    assert s.auto_link_threshold == 0.7
```

Replace with:

```python
def test_auto_link_threshold_defaults_to_0_8():
    """Default 0.8 — stricter than TF-IDF literature (0.7) so only highly
    confident matches become wiki-links. Must remain below
    similarity_threshold (0.85) used by check_interference."""
    s = _settings()
    assert s.auto_link_threshold == 0.8


def test_auto_link_threshold_below_interference_threshold():
    """Wiki-link threshold must be <= interference threshold — otherwise
    link generation would fire on pairs that are also duplicates, and the
    interference resolver would clean them up immediately."""
    s = _settings()
    assert s.auto_link_threshold <= s.similarity_threshold
```

**Step 2: Run**

```bash
uv run pytest tests/test_auto_link_threshold.py::test_auto_link_threshold_defaults_to_0_8 tests/test_auto_link_threshold.py::test_auto_link_threshold_below_interference_threshold -v
```
Expected: PASS.

**Step 3: Do NOT commit yet** — continue to Task 3.

---

### Task 3: Use Pydantic's ValidationError in tests (S-2)

**Files:**
- Modify: `tests/test_auto_link_threshold.py`

**Step 1: Update imports**

At the top of the file, add:

```python
from pydantic import ValidationError
```

**Step 2: Replace `pytest.raises(ValueError)` with `pytest.raises(ValidationError)`**

Find:

```python
def test_auto_link_threshold_rejects_below_zero():
    with pytest.raises(ValueError):
        _settings(auto_link_threshold=-0.1)


def test_auto_link_threshold_rejects_above_one():
    with pytest.raises(ValueError):
        _settings(auto_link_threshold=1.5)
```

Replace with:

```python
def test_auto_link_threshold_rejects_below_zero():
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=-0.1)


def test_auto_link_threshold_rejects_above_one():
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=1.5)
```

**Step 3: Run**

```bash
uv run pytest tests/test_auto_link_threshold.py -v
```
Expected: all tests pass.

**Step 4: Do NOT commit yet** — continue to Task 4.

---

### Task 4: Enhance boundary coverage (S-3)

**Files:**
- Modify: `tests/test_auto_link_threshold.py`

**Step 1: Add near-boundary tests**

Append to `tests/test_auto_link_threshold.py`:

```python
def test_auto_link_threshold_accepts_near_zero():
    """Values just above the lower bound should be accepted."""
    s = _settings(auto_link_threshold=0.01)
    assert s.auto_link_threshold == 0.01


def test_auto_link_threshold_accepts_near_one():
    """Values just below the upper bound should be accepted."""
    s = _settings(auto_link_threshold=0.99)
    assert s.auto_link_threshold == 0.99


def test_auto_link_threshold_rejects_infinity():
    """Infinity is not a valid threshold."""
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=float("inf"))


def test_auto_link_threshold_rejects_nan():
    """NaN must not slip through — ge/le comparisons with NaN are False
    in Python, so Pydantic should reject it."""
    with pytest.raises(ValidationError):
        _settings(auto_link_threshold=float("nan"))
```

**Step 2: Run the full test file**

```bash
uv run pytest tests/test_auto_link_threshold.py -v
```
Expected: all pass (9 tests total — original 4 adjusted + 2 renamed/added in Task 2 + 4 new).

**Step 3: Run full suite to verify no regressions**

```bash
uv run pytest 2>&1 | tail -3
```
Expected: 147+ passed.

**Step 4: Commit everything at once**

```bash
git add src/neuro_mcp/config.py tests/test_auto_link_threshold.py
git commit -m "$(cat <<'EOF'
fix: document similarity thresholds and tighten auto_link_threshold default

- Add inline comments distinguishing similarity_threshold (0.85, interference)
  from auto_link_threshold (0.8, wiki-links)
- Raise auto_link_threshold default from 0.7 to 0.8 for stricter "confident
  match" semantics — must stay below similarity_threshold to avoid fighting
  the interference resolver
- Invariant test: auto_link_threshold <= similarity_threshold
- Tests use Pydantic ValidationError instead of generic ValueError
- New boundary tests: near-0, near-1, infinity, NaN rejection

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Summary

| Task | Scope | Time |
|------|-------|------|
| 1. Inline comments + raise default to 0.8 | Config | 3 min |
| 2. Update default test + invariant test | Test | 3 min |
| 3. Use `ValidationError` specifically | Test | 2 min |
| 4. Near-boundary + inf/NaN tests | Test | 3 min |

**Total: ~11 min, 1 commit.**

**Test count change:** 5 tests before → 9 tests after (+4 new, 1 renamed with updated assertion).

## Notes

- **Why 0.8 specifically?** Between the TF-IDF literature default (0.7) and the existing interference threshold (0.85). Gives a clear ordering invariant — auto-link fires first, interference fires second — and leaves room for both thresholds to be tuned independently.
- **Invariant test matters:** If a future user ever raises `auto_link_threshold` above `similarity_threshold`, they'd have wiki-links firing on content the interference resolver also flags as duplicates. The test catches that contradiction at config-load time.
- **NaN test is a real concern:** Python's `ge`/`le` comparison with NaN silently returns False, but Pydantic's v2 numeric validators explicitly reject NaN for bounded fields. Worth testing to prevent surprises.
