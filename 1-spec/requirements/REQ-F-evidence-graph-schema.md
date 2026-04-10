# REQ-F-evidence-graph-schema

**Status:** Draft
**Priority:** Should-have
**Type:** Functional
**Source:** [[1-spec/goals/GOAL-evidence-graph|GOAL-evidence-graph]]

## Description

Add a typed evidence graph layer to storage where notes, code chunks, manifests, and claims are nodes with precision-weighted edges. The graph enables neighborhood-based search reranking and multi-hop contradiction propagation.

## Acceptance Criteria

- [ ] SQLite tables for evidence_node (id, node_type, doc_id, precision, freshness) and evidence_edge (source_id, target_id, edge_type, edge_precision, contradiction_score)
- [ ] Edge types include: references, claims, supersedes, contradicts, belongs_to, depends_on
- [ ] service.refresh() builds/updates the graph from linked_paths, claimed_dependencies, and import chains
- [ ] search.py supports optional graph-aware reranking (Personalized PageRank or weighted neighborhood expansion)
- [ ] brain_get_related uses graph edges when available, falls back to embedding similarity
- [ ] Graph is optional — system works without it ([[1-spec/constraints/CON-offline-first|CON-offline-first]], [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]])

## Related Artifacts

Goal: [[1-spec/goals/GOAL-evidence-graph|GOAL-evidence-graph]]
Constraint: [[1-spec/constraints/CON-backwards-compatible|CON-backwards-compatible]], [[1-spec/constraints/CON-offline-first|CON-offline-first]]
