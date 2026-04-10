# GOAL-evidence-graph

**Description**: Add a typed evidence graph layer where notes, code chunks, manifests, and claims become nodes with precision-weighted edges, enabling graph-aware search reranking and multi-hop contradiction propagation.

**Status**: Draft

**Priority**: Should-have

**Source stakeholder**: [[1-spec/stakeholders|STK-ai-agent]], [[1-spec/stakeholders|STK-developer]]

## Success Criteria

- [ ] SQLite schema for nodes and edges with precision, freshness, edge_type
- [ ] Search reranks using graph neighborhood context
- [ ] brain_get_related uses graph edges, not just embedding similarity
- [ ] Contradictions propagate over evidence paths

## Related Artifacts

- Requirements: [[1-spec/requirements/REQ-F-evidence-graph-schema|REQ-F-evidence-graph-schema]]
