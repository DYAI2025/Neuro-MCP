# DEC-code-wins-source-of-truth

**Status:** Active
**Date:** 2026-04-10
**Trigger:** When reconcile detects brain vs code disagreement

## Decision

Code is always the source of truth when notes and code disagree. The reconcile function returns the contradiction and marks code as authoritative. Notes capture rationale, intent, and semantic memory; code captures current implementation state.

## Rationale

Notes can silently go stale. Code is always current (it either compiles/runs or it doesn't). Treating code as ground truth prevents the knowledge base from becoming a source of hallucination.

## Enforcement

- reconcile.py must set source_of_truth: "code" when disagreement is detected
- Search results from code always get freshness: current and source_precision: 1.0
- Brain notes that contradict code are marked with contradiction_detected: true
