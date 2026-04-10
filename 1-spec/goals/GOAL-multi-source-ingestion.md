# GOAL-multi-source-ingestion

**Description**: Ingest project knowledge from multiple source families — repository content, commits, PRs, agent conversations, documents, architecture plans — and relate them to existing context instead of storing isolated fragments.

**Status**: Draft

**Priority**: Should-have

**Source stakeholder**: [[1-spec/stakeholders|STK-developer]], [[1-spec/stakeholders|STK-ai-agent]]

## Success Criteria

- [ ] Ingestion supports: markdown notes, code files, git commits, package manifests (existing)
- [ ] New: PR descriptions, agent session summaries, and architecture docs as distinct source types
- [ ] New knowledge is related to existing context, not stored as isolated fragments
- [ ] Conflicting cross-source information is explicitly marked

## Related Artifacts

- Requirements: [[1-spec/requirements/REQ-F-multi-source-knowledge-ingestion|REQ-F-multi-source-knowledge-ingestion]]
