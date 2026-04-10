# Phase 1: Foundation Fixes — Manual Test Runbook

## Prerequisites

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
uv sync --extra mcp --extra dev
```

## Test 1: Decay Defaults Consistency

Verify that get_note returns correct type-based decay for notes without explicit decay_class.

```bash
# Create test notes without decay_class
mkdir -p /tmp/test-brain
echo -e "---\ntitle: Test Inbox\ntype: inbox\nstatus: active\n---\nContent" > /tmp/test-brain/inbox-note.md
echo -e "---\ntitle: Test Bug\ntype: bug\nstatus: active\n---\nContent" > /tmp/test-brain/bug-note.md
echo -e "---\ntitle: Test ADR\ntype: adr\nstatus: active\n---\nContent" > /tmp/test-brain/adr-note.md

# Index and check
uv run neuro-mcp --brain-root /tmp/test-brain --code-root /tmp/test-brain get-note inbox-note.md
# Expected: decay_class should resolve based on type (inbox → 7d behavior)
```

## Test 2: GC --apply Mutations

Verify that gc --apply actually writes to frontmatter.

```bash
# Create a stale inbox note (no last_verified)
mkdir -p /tmp/test-brain
echo -e "---\ntitle: Stale Inbox\ntype: inbox\nstatus: active\n---\nOld content" > /tmp/test-brain/stale.md

# Dry run — should show archive candidate but not change file
uv run neuro-mcp --brain-root /tmp/test-brain --code-root /tmp/test-brain gc
cat /tmp/test-brain/stale.md
# Expected: status still "active"

# Apply — should mutate frontmatter
uv run neuro-mcp --brain-root /tmp/test-brain --code-root /tmp/test-brain gc --apply
cat /tmp/test-brain/stale.md
# Expected: status changed to "archived", archived_at timestamp present
```

## Test 3: Automated Tests

```bash
uv run pytest tests/test_decay_defaults_consistency.py tests/test_gc_apply.py -v
# Expected: All pass
```

## Cleanup

```bash
rm -rf /tmp/test-brain
```
