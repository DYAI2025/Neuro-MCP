# GOAL-evidence-graph

**Description**: Add a typed evidence graph layer where notes, code chunks, manifests, and claims become nodes with precision-weighted edges, enabling graph-aware search reranking and multi-hop contradiction propagation.

**Status**: Draft

**Priority**: Should-have

**Source stakeholder**: [STK-ai-agent](../stakeholders.md), [STK-developer](../stakeholders.md)

## Success Criteria

- [ ] SQLite schema for nodes and edges with precision, freshness, edge_type
- [ ] Search reranks using graph neighborhood context
- [ ] brain_get_related uses graph edges, not just embedding similarity
- [ ] Contradictions propagate over evidence paths

## Related Artifacts

- Requirements: _to be created_
