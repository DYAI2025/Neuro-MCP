# GOAL-evidence-network

**Status:** Draft
**Priority:** Should-have
**Source Stakeholder:** STK-developer, STK-ai-agent

## Description

Evolve the dual index into a precision-weighted evidence graph where notes, code chunks, manifests, commits, and claims are typed nodes with weighted edges. Retrieval becomes evidence-weighted neighborhood search, enabling multi-hop answers and contradiction propagation.

## Success Criteria

- [ ] Evidence graph schema exists in storage (nodes + edges with precision, freshness, edge_type)
- [ ] Search reranks results using graph context (not just document-level scores)
- [ ] brain_get_related uses graph neighborhood (not just embedding similarity)
- [ ] Contradiction scores propagate over evidence paths (not just local note vs code)

## Related Artifacts

Requirements: _none yet_
