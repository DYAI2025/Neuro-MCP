# NeuroMCP v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the 7 Must-have and 3 Should-have goals from the v2 specification, turning NeuroMCP from a dual search index into a self-maintaining knowledge discipline engine.

**Architecture:** Each phase builds on the previous, keeping all 77 existing tests green. New features are added via TDD in the core-engine component (Python), with MCP tool exposure in the mcp-server component. The watcher pipeline orchestrates all stages. Evidence graph is optional and additive.

**Tech Stack:** Python 3.11+, uv, SQLite, pytest, sentence-transformers (optional), FastMCP, Starlette

---

## Status Legend

| Status | Meaning |
|--------|---------|
| `Todo` | Not started |
| `In Progress` | Currently being worked on |
| `Done` | Completed and tested |
| `Blocked` | Waiting on another task |

## Priority Legend

| Priority | Meaning |
|----------|---------|
| P0 | Infrastructure / prerequisite |
| P1 | Must-have goal |
| P2 | Should-have goal |

---

## Task Tables

### Core Engine

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-decay-defaults-shared-map | Extract DEFAULT_DECAY_BY_TYPE into shared location, use in get_note and scan_brain | P1 | Todo | [REQ-F-decay-defaults-consistency](../1-spec/requirements/REQ-F-decay-defaults-consistency.md) | - | 2026-04-10 | freshness.py already has TYPE_DEFAULT_DECAY |
| TASK-decay-defaults-tests | Test get_note uses type-based decay (inbox=7d, bug=14d, arch=90d, adr=immutable) | P1 | Todo | [REQ-F-decay-defaults-consistency](../1-spec/requirements/REQ-F-decay-defaults-consistency.md) | TASK-decay-defaults-shared-map | 2026-04-10 | |
| TASK-gc-frontmatter-writer | gc --apply calls execute_gc_actions to write status:archived to frontmatter | P1 | Todo | [REQ-F-gc-apply-mutations](../1-spec/requirements/REQ-F-gc-apply-mutations.md) | - | 2026-04-10 | execute_gc_actions exists in gc.py but is not wired to service.gc() |
| TASK-gc-mutation-logging | Log each GC mutation with timestamp, reason, previous status | P1 | Todo | [REQ-F-gc-apply-mutations](../1-spec/requirements/REQ-F-gc-apply-mutations.md) | TASK-gc-frontmatter-writer | 2026-04-10 | |
| TASK-gc-idempotency-tests | Test gc --apply idempotent, dry-run unchanged, mutations logged | P1 | Todo | [REQ-F-gc-apply-mutations](../1-spec/requirements/REQ-F-gc-apply-mutations.md) | TASK-gc-mutation-logging | 2026-04-10 | |
| TASK-labile-linked-paths-check | In refresh(), check linked_paths existence when auto_mark_labile=true | P1 | Todo | [REQ-F-labile-auto-mark](../1-spec/requirements/REQ-F-labile-auto-mark.md) | - | 2026-04-10 | Needs auto_mark_labile field in Settings |
| TASK-labile-frontmatter-write | Write status:labile + reason to frontmatter via writer.py | P1 | Todo | [REQ-F-labile-auto-mark](../1-spec/requirements/REQ-F-labile-auto-mark.md) | TASK-labile-linked-paths-check | 2026-04-10 | |
| TASK-labile-tests | Test: missing file→labile, existing→no change, disabled→no change | P1 | Todo | [REQ-F-labile-auto-mark](../1-spec/requirements/REQ-F-labile-auto-mark.md) | TASK-labile-frontmatter-write | 2026-04-10 | |
| TASK-stc-refresh-integration | Call synaptic_tagging check from service.refresh() after brain scan | P1 | Todo | [REQ-F-stc-promotion-queue](../1-spec/requirements/REQ-F-stc-promotion-queue.md) | - | 2026-04-10 | synaptic_tagging.py exists but not called from refresh() |
| TASK-stc-frontmatter-promote | Write promoted decay_class to frontmatter, log promotion | P1 | Todo | [REQ-F-stc-promotion-queue](../1-spec/requirements/REQ-F-stc-promotion-queue.md) | TASK-stc-refresh-integration | 2026-04-10 | |
| TASK-stc-digest-display | Show promotion candidates and recent promotions in digest() | P1 | Todo | [REQ-F-stc-promotion-queue](../1-spec/requirements/REQ-F-stc-promotion-queue.md) | TASK-stc-frontmatter-promote | 2026-04-10 | |
| TASK-stc-promotion-tests | Test: inbox+overlap→promote, old inbox→no, non-inbox→no | P1 | Todo | [REQ-F-stc-promotion-queue](../1-spec/requirements/REQ-F-stc-promotion-queue.md) | TASK-stc-digest-display | 2026-04-10 | |
| TASK-watcher-config-flags | Add enable_stc, enable_auto_labile, enable_auto_reconcile to Settings | P1 | Todo | [REQ-F-watcher-orchestration](../1-spec/requirements/REQ-F-watcher-orchestration.md) | - | 2026-04-10 | |
| TASK-watcher-pipeline-chain | Extend watch_forever: refresh → STC → labile → reconcile based on flags | P1 | Todo | [REQ-F-watcher-orchestration](../1-spec/requirements/REQ-F-watcher-orchestration.md) | TASK-watcher-config-flags, TASK-labile-tests, TASK-stc-promotion-tests | 2026-04-10 | |
| TASK-watcher-error-isolation | Wrap each pipeline stage in try/except, log, continue | P1 | Todo | [REQ-F-watcher-orchestration](../1-spec/requirements/REQ-F-watcher-orchestration.md) | TASK-watcher-pipeline-chain | 2026-04-10 | |
| TASK-watcher-pipeline-tests | Test: all stages run, error isolation, flags disable stages | P1 | Todo | [REQ-F-watcher-orchestration](../1-spec/requirements/REQ-F-watcher-orchestration.md) | TASK-watcher-error-isolation | 2026-04-10 | |
| TASK-recon-tx-schema | Add reconsolidation_tx table to storage.py | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | - | 2026-04-10 | Auto-create on startup |
| TASK-recon-tx-create | reconcile() creates reconsolidation_tx when contradiction_score > threshold | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | TASK-recon-tx-schema | 2026-04-10 | |
| TASK-recon-tx-labile-write | Write status:labile + labile_since + labile_reasons to frontmatter | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | TASK-recon-tx-create | 2026-04-10 | |
| TASK-recon-tx-resolve | Add restabilize() and supersede() methods, update tx + frontmatter | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | TASK-recon-tx-labile-write | 2026-04-10 | |
| TASK-recon-tx-digest | Show open reconsolidation_tx count in digest() and brain_status | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | TASK-recon-tx-resolve | 2026-04-10 | |
| TASK-recon-tx-audit-log | Log all state transitions with timestamp and evidence | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | TASK-recon-tx-digest | 2026-04-10 | |
| TASK-recon-tx-tests | Test: create tx, labile write, restabilize, supersede, digest count | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | TASK-recon-tx-audit-log | 2026-04-10 | |
| TASK-ingest-auto-reindex | After brain_ingest_note, trigger incremental index update | P1 | Todo | [REQ-F-bidirectional-memory](../1-spec/requirements/REQ-F-bidirectional-memory.md) | - | 2026-04-10 | |
| TASK-ingest-source-type | Add source_type to frontmatter on ingest (agent-session, manual, etc) | P1 | Todo | [REQ-F-bidirectional-memory](../1-spec/requirements/REQ-F-bidirectional-memory.md) | TASK-ingest-auto-reindex | 2026-04-10 | |
| TASK-watcher-reconcile-overlap | Watcher finds notes with overlapping linked_paths, triggers reconcile | P1 | Todo | [REQ-F-bidirectional-memory](../1-spec/requirements/REQ-F-bidirectional-memory.md) | TASK-watcher-pipeline-chain | 2026-04-10 | |
| TASK-bidirectional-tests | Test: ingest→searchable, source_type written, watcher→reconcile | P1 | Todo | [REQ-F-bidirectional-memory](../1-spec/requirements/REQ-F-bidirectional-memory.md) | TASK-watcher-reconcile-overlap | 2026-04-10 | |
| TASK-context-bootstrap-cmd | Add bootstrap CLI: index + digest + reconcile + gap report | P1 | Todo | [REQ-F-context-bootstrap-existing-projects](../1-spec/requirements/REQ-F-context-bootstrap-existing-projects.md) | - | 2026-04-10 | |
| TASK-context-bootstrap-gaps | Record unresolved gaps (missing manifests, unlinked notes) | P1 | Todo | [REQ-F-context-bootstrap-existing-projects](../1-spec/requirements/REQ-F-context-bootstrap-existing-projects.md) | TASK-context-bootstrap-cmd | 2026-04-10 | |
| TASK-context-bootstrap-tests | Test: bootstrap empty project, bootstrap with gaps | P1 | Todo | [REQ-F-context-bootstrap-existing-projects](../1-spec/requirements/REQ-F-context-bootstrap-existing-projects.md) | TASK-context-bootstrap-gaps | 2026-04-10 | |
| TASK-evidence-node-edge-schema | Add evidence_node and evidence_edge tables | P2 | Todo | [REQ-F-evidence-graph-schema](../1-spec/requirements/REQ-F-evidence-graph-schema.md) | - | 2026-04-10 | |
| TASK-evidence-graph-build | Build graph edges from linked_paths/claimed_deps during refresh() | P2 | Todo | [REQ-F-evidence-graph-schema](../1-spec/requirements/REQ-F-evidence-graph-schema.md) | TASK-evidence-node-edge-schema | 2026-04-10 | |
| TASK-evidence-graph-rerank | Optional graph-aware reranking in search.py | P2 | Todo | [REQ-F-evidence-graph-schema](../1-spec/requirements/REQ-F-evidence-graph-schema.md) | TASK-evidence-graph-build | 2026-04-10 | |
| TASK-evidence-related-graph | brain_get_related uses graph edges, falls back to embeddings | P2 | Todo | [REQ-F-evidence-graph-schema](../1-spec/requirements/REQ-F-evidence-graph-schema.md) | TASK-evidence-graph-rerank | 2026-04-10 | |
| TASK-evidence-graph-tests | Test: edges created, reranking, related fallback, graph optional | P2 | Todo | [REQ-F-evidence-graph-schema](../1-spec/requirements/REQ-F-evidence-graph-schema.md) | TASK-evidence-related-graph | 2026-04-10 | |
| TASK-recency-assessment | Classify artifacts as current/superseded/ambiguous with confidence | P2 | Todo | [REQ-REL-recency-and-evolution-assessment](../1-spec/requirements/REQ-REL-recency-and-evolution-assessment.md) | - | 2026-04-10 | |
| TASK-coherence-check | Flag interpretations conflicting with broader context | P2 | Todo | [REQ-F-coherence-and-single-source-of-truth](../1-spec/requirements/REQ-F-coherence-and-single-source-of-truth.md) | TASK-recency-assessment | 2026-04-10 | |
| TASK-multi-source-types | Add source type registry for PR descriptions, agent summaries | P2 | Todo | [REQ-F-multi-source-knowledge-ingestion](../1-spec/requirements/REQ-F-multi-source-knowledge-ingestion.md) | - | 2026-04-10 | |
| TASK-multi-source-relation | Relate new knowledge to existing context, mark conflicts | P2 | Todo | [REQ-F-multi-source-knowledge-ingestion](../1-spec/requirements/REQ-F-multi-source-knowledge-ingestion.md) | TASK-multi-source-types | 2026-04-10 | |
| TASK-should-have-tests | Test: recency, coherence, multi-source, conflict marking | P2 | Todo | - | TASK-coherence-check, TASK-multi-source-relation, TASK-evidence-graph-tests | 2026-04-10 | |

### MCP Server

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-recon-mcp-tools | Expose approve_reconsolidation and explain_contradictions as MCP tools | P1 | Todo | [REQ-F-reconsolidation-transactions](../1-spec/requirements/REQ-F-reconsolidation-transactions.md) | TASK-recon-tx-tests | 2026-04-10 | |
| TASK-bootstrap-mcp-tool | Expose context_bootstrap as MCP tool | P1 | Todo | [REQ-F-context-bootstrap-existing-projects](../1-spec/requirements/REQ-F-context-bootstrap-existing-projects.md) | TASK-context-bootstrap-tests | 2026-04-10 | |

### Deploy & Operations

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-phase-1-manual-testing | Create 4-deploy/runbooks/phase-1-foundation.md with test scenarios | P0 | Todo | - | TASK-gc-idempotency-tests, TASK-decay-defaults-tests | 2026-04-10 | |
| TASK-phase-2-manual-testing | Update runbook with labile + STC test scenarios | P0 | Todo | - | TASK-labile-tests, TASK-stc-promotion-tests | 2026-04-10 | |
| TASK-phase-3-manual-testing | Update runbook with watcher pipeline scenarios | P0 | Todo | - | TASK-watcher-pipeline-tests | 2026-04-10 | |
| TASK-phase-4-manual-testing | Update runbook with reconsolidation + MCP tool scenarios | P0 | Todo | - | TASK-recon-mcp-tools | 2026-04-10 | |
| TASK-phase-5-manual-testing | Update runbook with bidirectional memory + bootstrap scenarios | P0 | Todo | - | TASK-bidirectional-tests, TASK-bootstrap-mcp-tool | 2026-04-10 | |
| TASK-phase-6-manual-testing | Update runbook with evidence graph + coherence scenarios | P0 | Todo | - | TASK-should-have-tests | 2026-04-10 | |

---

## Execution Plan

### Phase 1: Foundation Fixes

**Capabilities delivered:**
- `get_note()` uses consistent type-based decay defaults instead of hard 30d fallback
- `gc --apply` actually mutates frontmatter (writes `status: archived`), idempotent and logged
- Foundation for all subsequent phases is stable

**Tasks:**
1. TASK-decay-defaults-shared-map
2. TASK-decay-defaults-tests
3. TASK-gc-frontmatter-writer
4. TASK-gc-mutation-logging
5. TASK-gc-idempotency-tests
6. TASK-phase-1-manual-testing

### Phase 2: Labile State Machine

**Capabilities delivered:**
- Notes with deleted linked files auto-marked `labile` (when `auto_mark_labile: true`)
- STC promotes inbox notes corroborated by code changes within 48h
- Agents see invalidated knowledge immediately in search results

**Tasks:**
1. TASK-labile-linked-paths-check
2. TASK-labile-frontmatter-write
3. TASK-labile-tests
4. TASK-stc-refresh-integration
5. TASK-stc-frontmatter-promote
6. TASK-stc-digest-display
7. TASK-stc-promotion-tests
8. TASK-phase-2-manual-testing

### Phase 3: Watcher Pipeline Orchestration

**Capabilities delivered:**
- File watcher chains: refresh → STC → labile marking → reconcile trigger
- Each stage independently configurable on/off via config.yaml
- Errors in one stage don't block subsequent stages

**Tasks:**
1. TASK-watcher-config-flags
2. TASK-watcher-pipeline-chain
3. TASK-watcher-error-isolation
4. TASK-watcher-pipeline-tests
5. TASK-phase-3-manual-testing

### Phase 4: Reconsolidation Transactions

**Capabilities delivered:**
- Contradictions create persistent `reconsolidation_tx` records in SQLite
- Notes transition `active → labile` with evidence, reason, deadline
- Resolution paths: `restabilize` (update + verify) or `supersede` (link replacement)
- New MCP tools: `approve_reconsolidation`, `explain_contradictions`
- `digest()` and `brain_status` show open transaction count

**Tasks:**
1. TASK-recon-tx-schema
2. TASK-recon-tx-create
3. TASK-recon-tx-labile-write
4. TASK-recon-tx-resolve
5. TASK-recon-tx-digest
6. TASK-recon-tx-audit-log
7. TASK-recon-tx-tests
8. TASK-recon-mcp-tools
9. TASK-phase-4-manual-testing

### Phase 5: Bidirectional Memory & Context Bootstrap

**Capabilities delivered:**
- `brain_ingest_note` triggers immediate re-indexing (no manual `index` needed)
- Notes track `source_type` (agent-session, manual, codebase-analysis)
- Watcher detects code changes, auto-reconciles affected brain notes
- `bootstrap` CLI command: index + digest + reconcile + gap report in one pass
- New MCP tool: `context_bootstrap`

**Tasks:**
1. TASK-ingest-auto-reindex
2. TASK-ingest-source-type
3. TASK-watcher-reconcile-overlap
4. TASK-bidirectional-tests
5. TASK-context-bootstrap-cmd
6. TASK-context-bootstrap-gaps
7. TASK-context-bootstrap-tests
8. TASK-bootstrap-mcp-tool
9. TASK-phase-5-manual-testing

### Phase 6: Should-Have Extensions

**Capabilities delivered:**
- Evidence graph schema (nodes + edges with precision, freshness, edge_type)
- Graph-aware search reranking (weighted neighborhood expansion)
- `brain_get_related` uses graph edges when available
- Recency/evolution assessment with confidence for missing timestamps
- Coherence checks flag conflicting interpretations
- Multi-source ingestion framework (PR descriptions, agent summaries)

**Tasks:**
1. TASK-evidence-node-edge-schema
2. TASK-evidence-graph-build
3. TASK-evidence-graph-rerank
4. TASK-evidence-related-graph
5. TASK-evidence-graph-tests
6. TASK-recency-assessment
7. TASK-coherence-check
8. TASK-multi-source-types
9. TASK-multi-source-relation
10. TASK-should-have-tests
11. TASK-phase-6-manual-testing

---

## Summary

| Phase | Name | Tasks | Goal Coverage |
|-------|------|-------|---------------|
| 1 | Foundation Fixes | 6 | GOAL-reconsolidation-workflow (partial), GOAL-gc-real-mutations |
| 2 | Labile State Machine | 8 | GOAL-labile-auto-marking, GOAL-stc-promotion |
| 3 | Watcher Pipeline | 5 | GOAL-watcher-pipeline |
| 4 | Reconsolidation Transactions | 9 | GOAL-reconsolidation-workflow (complete) |
| 5 | Bidirectional Memory & Bootstrap | 9 | GOAL-bidirectional-memory, GOAL-context-bootstrap |
| 6 | Should-Have Extensions | 11 | GOAL-evidence-graph, GOAL-coherent-narrative, GOAL-multi-source-ingestion |
| **Total** | | **48 tasks** | **10/10 goals covered** |

## How to Update

When working on a task:
1. Set its Status to `In Progress`
2. Update the `Updated` column to today's date
3. When done, set Status to `Done`
4. Add any notes about decisions or issues encountered
