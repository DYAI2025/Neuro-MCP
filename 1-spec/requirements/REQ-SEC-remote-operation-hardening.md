# REQ-SEC-remote-operation-hardening

**Status:** Draft
**Priority:** Must-have
**Type:** Security
**Source:** [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]

## Description

When NeuroMCP runs beyond local development (streamable-HTTP MCP, shared machine, VPN-exposed), auth must be validated, tool calls audited, workspace boundaries enforced, and basic rate limits available. Unsafe config must be rejected at startup.

## Acceptance Criteria (maps to tasks 71-76)

- [ ] TASK-auth-config-validation: insecure auth/origin settings rejected at startup in remote mode
- [ ] TASK-tool-audit-log: MCP tool calls logged with actor/session/tool/result metadata
- [ ] TASK-rate-limit-guardrails: optional per-endpoint/tool request throttling
- [ ] TASK-sensitive-path-guard: path access outside configured workspace roots prevented
- [ ] TASK-deploy-reference-configs: hardened reverse-proxy/deploy examples for local and remote
- [ ] TASK-security-smoke-tests: unsafe config rejected, workspace escape blocked, audit log created

## Related Artifacts

Goal: [[1-spec/goals/GOAL-production-readiness|GOAL-production-readiness]]
