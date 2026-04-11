# NeuroMCP SDLC Scaffold Initialization Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bootstrap the ai-scrum-scaffold into the neuro-mcp repo, populate it with existing architecture knowledge and product vision requirements, and establish AI-first project management for the v2 roadmap.

**Architecture:** The ai-scrum-scaffold provides 4 SDLC phases (1-spec, 2-design, 3-code, 4-deploy) with CLAUDE.md-based agent instructions, decision records, and Claude skills. We overlay this onto the existing neuro-mcp Python codebase without disrupting it. The spec phase gets populated from the product vision documents (6-layer architecture, gap analysis, ranked extensions). The design phase gets populated from existing code architecture. The code phase maps to the existing `src/neuro_mcp/` modules plus the visual test lab.

**Tech Stack:** Python 3.11+, uv, SQLite, sentence-transformers, FastMCP, React/Vite (visual test lab), ai-scrum-scaffold (markdown SDLC)

---

## Pre-Requisites

- The ai-scrum-scaffold ZIP is already extracted at `/tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/`
- The neuro-mcp-project-architecture (visual test lab) ZIP is at `/tmp/neuro-arch/`
- Product vision docs are read and understood (see input docs)

---

### Task 1: Copy SDLC Scaffold Into Repo

**Files:**
- Create: `1-spec/` directory tree (goals, requirements, constraints, user-stories, assumptions templates)
- Create: `2-design/` directory tree (architecture.md, data-model.md, api-design.md)
- Create: `3-code/` directory tree (tasks.md, CLAUDE.code.md)
- Create: `4-deploy/` directory tree (runbooks)
- Create: `decisions/` directory tree (templates, PROCEDURES.md)
- Create: `.claude/skills/SDLC-*/` skill files
- Modify: `CLAUDE.md` — merge scaffold root instructions with existing content

**Step 1: Copy scaffold directories (excluding scaffold-specific files)**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean

# Copy SDLC phase directories
cp -r /tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/1-spec .
cp -r /tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/2-design .
cp -r /tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/3-code .
cp -r /tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/4-deploy .
cp -r /tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/decisions .

# Copy SDLC skills
cp -r /tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/.claude/skills/SDLC-* .claude/skills/
```

**Step 2: Remove scaffold example artifacts (keep templates only)**

Remove the example requirements, goals, constraints, and user stories that are specific to the scaffold's demo project (example project):

```bash
# Remove example spec artifacts (keep _template.md files)
rm -f 1-spec/requirements/REQ-F-*.md
rm -f 1-spec/goals/GOAL-*.md
rm -f 1-spec/constraints/CON-*.md
rm -f 1-spec/user-stories/US-*.md
```

**Step 3: Verify directory structure**

```bash
find 1-spec 2-design 3-code 4-deploy decisions .claude/skills/SDLC-* -type f | sort
```

Expected: template files in each phase, CLAUDE.phase.md files, SKILL.md files in .claude/skills/SDLC-*/.

**Step 4: Commit**

```bash
git add 1-spec/ 2-design/ 3-code/ 4-deploy/ decisions/ .claude/skills/SDLC-*/
git commit -m "feat: add ai-scrum-scaffold SDLC structure for project management"
```

---

### Task 2: Merge CLAUDE.md — Add SDLC Root Instructions

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Read current CLAUDE.md**

The existing CLAUDE.md has: Persistent Memory, Installation, Tests, CLI, Architecture, Key design constraints, Configuration sections.

**Step 2: Read scaffold CLAUDE.md for the sections to merge**

Read `/tmp/ai-scrum-scaffold/ai-scrum-scaffold-main/CLAUDE.md` — extract the `## Project Overview`, `## Repository Structure`, and `## Development Lifecycle` sections.

**Step 3: Add SDLC sections to CLAUDE.md**

Insert after the existing `## Configuration` section:

```markdown
## Project Overview

NeuroMCP is a production-oriented MCP server and local knowledge engine that keeps semantic notes useful over time by connecting them to the codebase they describe. It uses neuro-inspired concepts (freshness decay, reconsolidation, synaptic tagging, phasic/tonic modes) to maintain knowledge integrity.

### Current State

The core system is stable (v1): dual brain/code indexing, freshness model, reconciliation, MCP tools, HTTP/stdio transport. Development is in the **Specification phase** for v2 extensions: Reconsolidation Review Transactions, Precision-Weighted Evidence Graph, STC Promotion Queue, and Claim Engine.

## SDLC Structure

This project uses the [AI SDLC Scaffold](https://github.com/pangon/ai-sdlc-scaffold) for AI-first development:

- `1-spec/` — WHAT and WHY: goals, requirements, constraints, user stories
- `2-design/` — HOW: architecture, data model, API design
- `3-code/` — BUILD: component directories, tasks, source code
- `4-deploy/` — SHIP: runbooks, deployment procedures
- `decisions/` — Decision records (DEC-*.md + history)
- `.claude/skills/SDLC-*/` — Claude skills for each SDLC phase

Skills: `/SDLC-init`, `/SDLC-elicit`, `/SDLC-design`, `/SDLC-decompose`, `/SDLC-implementation-plan`, `/SDLC-execute-next-task`, `/SDLC-fix`, `/SDLC-status`
```

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: merge SDLC scaffold instructions into CLAUDE.md"
```

---

### Task 3: Populate Stakeholders

**Files:**
- Modify: `1-spec/stakeholders.md`

**Step 1: Read the stakeholders template**

```bash
cat 1-spec/stakeholders.md
```

**Step 2: Write stakeholders based on the product vision docs**

Replace placeholder content with:

```markdown
# Stakeholders

## STK-developer

**Role:** Solo developer / project owner
**Perspective:** Builds and maintains NeuroMCP, uses it daily for own projects
**Key needs:** Fast iteration, reliable freshness model, MCP integration that works across all AI clients
**Communication:** Direct (user = developer)

## STK-ai-agent

**Role:** AI agent (Claude, Cursor, custom agents) consuming NeuroMCP tools
**Perspective:** Needs grounded, verified project knowledge to avoid hallucination
**Key needs:** Reliable search results, source-of-truth verdicts, contradiction detection, ability to persist findings
**Communication:** MCP protocol (stdio/HTTP)

## STK-knowledge-worker

**Role:** End user maintaining an Obsidian/markdown knowledge vault
**Perspective:** Wants notes to stay accurate without manual audit effort
**Key needs:** Automatic freshness tracking, stale note detection, duplicate management, low maintenance overhead
**Communication:** CLI, MCP tools via Claude Desktop

## STK-team-onboarder

**Role:** New team member joining a project that uses NeuroMCP
**Perspective:** Needs to quickly understand project architecture and decisions
**Key needs:** Reconciled brain+code search, current architecture notes, contradiction-free knowledge base
**Communication:** MCP tools, CLI
```

**Step 3: Commit**

```bash
git add 1-spec/stakeholders.md
git commit -m "spec: define stakeholders for NeuroMCP v2"
```

---

### Task 4: Populate Goals (from Product Vision)

**Files:**
- Create: `1-spec/goals/GOAL-knowledge-discipline-engine.md`
- Create: `1-spec/goals/GOAL-self-maintaining-memory.md`
- Create: `1-spec/goals/GOAL-evidence-network.md`

**Step 1: Read the goals template**

```bash
cat 1-spec/goals/_template.md
```

**Step 2: Create GOAL-knowledge-discipline-engine.md**

```markdown
# GOAL-knowledge-discipline-engine

**Status:** Draft
**Priority:** Must-have
**Source Stakeholder:** STK-developer, STK-ai-agent

## Description

Transform NeuroMCP from a dual search index into a knowledge discipline engine that not only retrieves information but verifies it, detects contradictions, and maintains knowledge integrity through reconsolidation workflows.

## Success Criteria

- [ ] Contradictions detected by `reconcile` trigger persistent state transitions (active → labile → reviewed → restabilized/superseded)
- [ ] Reconsolidation transactions are auditable with evidence, reason, and resolution
- [ ] Stale/labile notes are downweighted in search but not hidden
- [ ] Source-of-truth verdicts propagate through related notes (not just local)

## Related Artifacts

Requirements: _none yet_
```

**Step 3: Create GOAL-self-maintaining-memory.md**

```markdown
# GOAL-self-maintaining-memory

**Status:** Draft
**Priority:** Must-have
**Source Stakeholder:** STK-developer, STK-knowledge-worker

## Description

Make the knowledge base self-maintaining: inbox notes get promoted or archived automatically based on salience, usage, and code corroboration. Monthly homeostasis prevents unbounded growth. GC applies real mutations, not just reports.

## Success Criteria

- [ ] STC promotion queue promotes inbox notes corroborated by code changes within 48h window
- [ ] Monthly homeostasis job renormalizes weights and demotes unused long-tail notes
- [ ] `gc --apply` actually mutates frontmatter status (not just report)
- [ ] `auto_mark_labile` config setting has real runtime effect
- [ ] Digest shows promotion candidates, homeostasis effects, and GC actions

## Related Artifacts

Requirements: _none yet_
```

**Step 4: Create GOAL-evidence-network.md**

```markdown
# GOAL-evidence-network

**Status:** Draft
**Priority:** Should-have
**Source Stakeholder:** STK-developer, STK-ai-agent

## Description

Evolve the dual index into a precision-weighted evidence graph where notes, code chunks, manifests, commits, and claims are typed nodes with weighted edges. Retrieval becomes evidence-weighted neighborhood search, enabling multi-hop answers and contradiction propagation.

## Success Criteria

- [ ] Evidence graph schema exists in storage (nodes + edges with precision, freshness, edge_type)
- [ ] Search reranks results using graph context (not just document-level scores)
- [ ] `brain_get_related` uses graph neighborhood (not just embedding similarity)
- [ ] Contradiction scores propagate over evidence paths (not just local note vs code)

## Related Artifacts

Requirements: _none yet_
```

**Step 5: Update goal index in CLAUDE.spec.md**

Read `1-spec/CLAUDE.spec.md` and add goal entries to the index table.

**Step 6: Commit**

```bash
git add 1-spec/goals/ 1-spec/CLAUDE.spec.md
git commit -m "spec: add v2 goals from product vision (discipline engine, self-maintaining, evidence network)"
```

---

### Task 5: Populate Constraints

**Files:**
- Create: `1-spec/constraints/CON-no-auto-delete.md`
- Create: `1-spec/constraints/CON-offline-first.md`
- Create: `1-spec/constraints/CON-backwards-compatible.md`

**Step 1: Read constraints template**

```bash
cat 1-spec/constraints/_template.md
```

**Step 2: Create CON-no-auto-delete.md**

```markdown
# CON-no-auto-delete

**Status:** Approved
**Category:** Operational
**Source Stakeholder:** STK-developer

## Description

NeuroMCP must never auto-delete note files. GC returns archive candidates first; content mutation requires explicit `--apply` flag. Reconsolidation may change status in frontmatter but must not silently rewrite note body text outside clearly marked draft sections.

## Rationale

Core design principle: the system may change status, may suggest, but must not silently overwrite human-written content. Trust is the product's foundation.

## Impact

All reconsolidation, GC, and interference resolution features must be two-stage: auto-state transitions yes, human-approved content mutation only.
```

**Step 3: Create CON-offline-first.md**

```markdown
# CON-offline-first

**Status:** Approved
**Category:** Technical
**Source Stakeholder:** STK-developer, STK-knowledge-worker

## Description

The default embedder must remain TF-IDF (deterministic, offline-safe). Semantic embeddings via sentence-transformers are opt-in. No feature may require an internet connection or external API for core functionality.

## Rationale

Privacy, reliability, and deployment simplicity. The system must work on a plane, behind a VPN, or in an air-gapped environment.

## Impact

All new features (evidence graph, claim engine, interference resolution) must work with TF-IDF alone. Semantic features enhance but never gate functionality.
```

**Step 4: Create CON-backwards-compatible.md**

```markdown
# CON-backwards-compatible

**Status:** Approved
**Category:** Technical
**Source Stakeholder:** STK-developer

## Description

v2 extensions must not break existing config.yaml files, CLI commands, or MCP tool signatures. New fields in frontmatter must have sensible defaults. New SQLite tables must be created via migration, not by dropping existing data.

## Rationale

Existing users with working setups must not be forced to reconfigure or reindex from scratch.

## Impact

All schema changes require migration logic. New frontmatter fields default gracefully. New CLI subcommands are additive.
```

**Step 5: Update constraint index in CLAUDE.spec.md**

**Step 6: Commit**

```bash
git add 1-spec/constraints/ 1-spec/CLAUDE.spec.md
git commit -m "spec: add core constraints (no-auto-delete, offline-first, backwards-compatible)"
```

---

### Task 6: Populate Requirements (High-Priority from Roadmap)

**Files:**
- Create: `1-spec/requirements/REQ-F-reconsolidation-transactions.md`
- Create: `1-spec/requirements/REQ-F-gc-apply-mutations.md`
- Create: `1-spec/requirements/REQ-F-stc-promotion-queue.md`
- Create: `1-spec/requirements/REQ-F-labile-auto-mark.md`
- Create: `1-spec/requirements/REQ-F-watcher-orchestration.md`
- Create: `1-spec/requirements/REQ-F-decay-defaults-consistency.md`

**Step 1: Read requirements template**

```bash
cat 1-spec/requirements/_template.md
```

**Step 2: Create REQ-F-reconsolidation-transactions.md**

```markdown
# REQ-F-reconsolidation-transactions

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-knowledge-discipline-engine

## Description

When `reconcile()` detects a contradiction above the configured threshold, the system must create a persistent reconsolidation transaction that transitions the affected note from `active` → `labile`. The transaction records: evidence (which code/manifest contradicts), reason, timestamp, and resolution deadline.

## Acceptance Criteria

- [ ] `reconcile()` creates a `reconsolidation_tx` record in SQLite when contradiction_score > threshold
- [ ] Affected note's frontmatter `status` is updated to `labile` with `labile_since` and `labile_reasons`
- [ ] `labile` notes are downweighted in search results (freshness score ≤ 0.40)
- [ ] `digest()` and `brain_status` show count of open reconsolidation transactions
- [ ] Resolution path exists: `restabilize` (update note + set current) or `supersede` (link to replacement note)
- [ ] All state transitions are logged in an audit trail

## Related Artifacts

Goal: GOAL-knowledge-discipline-engine
Constraint: CON-no-auto-delete
```

**Step 3: Create REQ-F-gc-apply-mutations.md**

```markdown
# REQ-F-gc-apply-mutations

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-self-maintaining-memory

## Description

`gc --apply` must actually mutate note frontmatter (update `status` field) instead of only reporting candidates. The mutation must be idempotent and auditable.

## Acceptance Criteria

- [ ] `gc --apply` writes `status: archived` to frontmatter of notes meeting archive criteria
- [ ] Each mutation is logged with timestamp, reason, and previous status
- [ ] `gc` without `--apply` remains a dry run (report only, no mutations)
- [ ] Mutations are idempotent (running twice produces same result)

## Related Artifacts

Goal: GOAL-self-maintaining-memory
Constraint: CON-no-auto-delete
```

**Step 4: Create REQ-F-stc-promotion-queue.md**

```markdown
# REQ-F-stc-promotion-queue

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-self-maintaining-memory

## Description

Implement a promotion queue based on Synaptic Tagging and Capture. Inbox notes created within the STC window (default 48h) whose `linked_paths` overlap with recently changed files (git diff) are promoted from `7d` → `30d` decay class.

## Acceptance Criteria

- [ ] `synaptic_tagging.py` is called from `service.refresh()` or `watcher.py` on each file change event
- [ ] Notes matching STC criteria have their `decay_class` updated in frontmatter
- [ ] Promotion is logged (which note, which overlapping files, old → new decay_class)
- [ ] `digest()` shows promotion candidates and recent promotions
- [ ] Only notes with `decay_class: 7d` (inbox) are eligible for promotion

## Related Artifacts

Goal: GOAL-self-maintaining-memory
```

**Step 5: Create REQ-F-labile-auto-mark.md**

```markdown
# REQ-F-labile-auto-mark

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-knowledge-discipline-engine

## Description

The `auto_mark_labile` config setting (already in config.example.yaml) must have real runtime effect. When enabled, notes whose `linked_paths` reference deleted files are automatically marked `status: labile`.

## Acceptance Criteria

- [ ] When `auto_mark_labile: true`, `refresh()` checks `linked_paths` existence
- [ ] Notes with missing linked files get `status: labile` written to frontmatter
- [ ] The change is logged with reason ("linked file deleted: path/to/file.ts")
- [ ] When `auto_mark_labile: false` (default), behavior is unchanged (report only)

## Related Artifacts

Goal: GOAL-knowledge-discipline-engine
Constraint: CON-backwards-compatible
```

**Step 6: Create REQ-F-watcher-orchestration.md**

```markdown
# REQ-F-watcher-orchestration

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-self-maintaining-memory

## Description

Wire `watcher.py` into a complete orchestration pipeline: file change → debounce → refresh → STC check → optional auto_mark_labile → optional reconsolidation trigger. Currently the watcher only calls `refresh()`.

## Acceptance Criteria

- [ ] `watch_forever()` calls `refresh()` then `synaptic_tagging_check()` on each change batch
- [ ] If `auto_mark_labile` is enabled, labile marking runs after refresh
- [ ] If reconsolidation is enabled, contradiction check runs after refresh
- [ ] Each stage is independently configurable (on/off in config.yaml)
- [ ] Errors in any stage are logged but do not block subsequent stages

## Related Artifacts

Goal: GOAL-self-maintaining-memory
```

**Step 7: Create REQ-F-decay-defaults-consistency.md**

```markdown
# REQ-F-decay-defaults-consistency

**Status:** Draft
**Priority:** Must-have
**Type:** Functional
**Source:** GOAL-knowledge-discipline-engine

## Description

`get_note()` must use the same type-based decay defaults as the indexer. Currently it falls back to a hard 30d default, diverging from the documented type-based defaults (inbox=7d, bug=14d, architecture=90d, adr=immutable).

## Acceptance Criteria

- [ ] `get_note()` resolves decay_class using the same logic as `scan_brain_documents()`
- [ ] Both share a single `DEFAULT_DECAY_BY_TYPE` mapping (DRY)
- [ ] Notes without explicit `decay_class` get the type-based default, not hard 30d
- [ ] Existing tests for freshness scoring still pass

## Related Artifacts

Goal: GOAL-knowledge-discipline-engine
Constraint: CON-backwards-compatible
```

**Step 8: Update requirement index in CLAUDE.spec.md**

**Step 9: Commit**

```bash
git add 1-spec/requirements/ 1-spec/CLAUDE.spec.md
git commit -m "spec: add 6 must-have requirements from v2 roadmap"
```

---

### Task 7: Populate Design Phase From Existing Architecture

**Files:**
- Modify: `2-design/architecture.md`
- Modify: `2-design/data-model.md`
- Modify: `2-design/api-design.md`

**Step 1: Read existing CLAUDE.md architecture section and source files**

Read the Architecture section from `CLAUDE.md` and the key source files to extract the current design:

```bash
head -50 src/neuro_mcp/service.py
head -50 src/neuro_mcp/storage.py
head -30 src/neuro_mcp/models.py
head -50 src/neuro_mcp/server.py
```

**Step 2: Write architecture.md**

Populate `2-design/architecture.md` with:
- System overview (6-layer target from product vision, current state per layer)
- Component diagram (service.py, storage.py, search.py, freshness.py, reconcile.py, reconsolidation.py, synaptic_tagging.py, interference.py, watcher.py, server.py, notes.py, codebase.py)
- Data flow for indexing (refresh pipeline)
- Data flow for search (query → retrieve → verify → judge → answer)
- Data flow for reconciliation
- Integration points (MCP stdio/HTTP, file watcher, git)

Source: existing CLAUDE.md Architecture section + product vision "6 Schichten" document.

**Step 3: Write data-model.md**

Populate `2-design/data-model.md` with:
- `DocumentRecord` schema (from models.py)
- `NoteMetadata` schema (from models.py)
- SQLite tables (from storage.py)
- Frontmatter schema (from GUIDE.md)
- Proposed v2 additions: `reconsolidation_tx` table, `evidence_edge` table, `promotion_log` table

**Step 4: Write api-design.md**

Populate `2-design/api-design.md` with:
- MCP tools (all 9 current tools with params and return types)
- Proposed v2 tools: `verify_claim`, `explain_contradictions`, `propose_note_patch`, `approve_reconsolidation`
- CLI commands (from CLAUDE.md CLI section)
- HTTP endpoints (/healthz, /readyz, /mcp, /.well-known/*)

**Step 5: Commit**

```bash
git add 2-design/
git commit -m "design: populate architecture, data model, and API design from existing system"
```

---

### Task 8: Decompose Into Components

**Files:**
- Create: `3-code/core-engine/CLAUDE.component.md`
- Create: `3-code/mcp-server/CLAUDE.component.md`
- Create: `3-code/visual-test-lab/CLAUDE.component.md`
- Modify: `3-code/CLAUDE.code.md`

**Step 1: Identify components from architecture**

Based on the architecture, three components:

| Component | Responsibility | Technology | Interfaces |
|-----------|---------------|------------|------------|
| core-engine | Indexing, search, freshness, reconciliation, reconsolidation, STC, GC, interference | Python, SQLite, TF-IDF, sentence-transformers | Python class API (NeuroMCPService) |
| mcp-server | MCP protocol layer, HTTP transport, auth, tool exposure | Python, FastMCP, Starlette, uvicorn | MCP stdio/HTTP ↔ core-engine |
| visual-test-lab | Deterministic GUI for testing neuro-MCP knowledge behaviors | React, Vite, TypeScript | HTTP/SSE ↔ mcp-server |

**Step 2: Create core-engine/CLAUDE.component.md**

```markdown
# Core Engine

**Responsibility**: Indexing, search, freshness scoring, reconciliation, reconsolidation, synaptic tagging, garbage collection, and interference management.

**Technology**: Python 3.11+, SQLite, TF-IDF (scikit-learn), sentence-transformers (optional)

## Interfaces

- Python class API with `mcp-server`: `NeuroMCPService` methods (search_brain, search_code, reconcile, digest, gc, get_note, get_related, ingest, check_interference, mode_detect)

## Source Files

- `src/neuro_mcp/service.py` — orchestrator
- `src/neuro_mcp/storage.py` — SQLite persistence
- `src/neuro_mcp/search.py` — hybrid search scoring
- `src/neuro_mcp/freshness.py` — decay and freshness model
- `src/neuro_mcp/reconcile.py` — brain vs code cross-check
- `src/neuro_mcp/reconsolidation.py` — mismatch-triggered state transitions
- `src/neuro_mcp/synaptic_tagging.py` — STC promotion logic
- `src/neuro_mcp/interference.py` — duplicate/conflict detection
- `src/neuro_mcp/notes.py` — brain vault scanner
- `src/neuro_mcp/codebase.py` — code scanner and manifest parser
- `src/neuro_mcp/embeddings.py` — TF-IDF + semantic embedders
- `src/neuro_mcp/models.py` — data models (DocumentRecord, NoteMetadata, etc.)
- `src/neuro_mcp/config.py` — Settings model
- `src/neuro_mcp/watcher.py` — file system watcher
- `src/neuro_mcp/git_utils.py` — git diff analysis for mode detection
- `src/neuro_mcp/writer.py` — frontmatter writer

## Requirements Addressed

All REQ-F-* requirements (reconsolidation-transactions, gc-apply-mutations, stc-promotion-queue, labile-auto-mark, watcher-orchestration, decay-defaults-consistency)
```

**Step 3: Create mcp-server/CLAUDE.component.md**

```markdown
# MCP Server

**Responsibility**: Expose core engine functionality as MCP tools over stdio and streamable-HTTP transports. Handle authentication, origin validation, and health endpoints.

**Technology**: Python, FastMCP, Starlette, uvicorn

## Interfaces

- MCP protocol with AI clients (Claude Desktop, Cursor, custom agents): 9 tools + 1 resource + 1 prompt
- HTTP endpoints: /healthz, /readyz, /mcp, /.well-known/oauth-protected-resource
- Python class API with core-engine: imports and calls NeuroMCPService

## Source Files

- `src/neuro_mcp/server.py` — MCP app builder, tool definitions, middleware
- `src/neuro_mcp/cli.py` — CLI entry point, config loading, serve command
```

**Step 4: Create visual-test-lab/CLAUDE.component.md**

```markdown
# Visual Test Lab

**Responsibility**: Deterministic, replayable GUI for testing NeuroMCP knowledge behaviors. Provides graph visualization, scenario playback, event timeline, and before/after diff panels.

**Technology**: React 18, Vite, TypeScript, vitest

## Interfaces

- HTTP/SSE with mcp-server: simulation adapter (currently simulated, swap-in point at adapter.ts)

## Source Files (from neuro-mcp-project-architecture.zip)

- `src/lab/engine.ts` — scenario execution engine
- `src/lab/scenarios.ts` — 10 baseline scenarios
- `src/lab/adapter.ts` — backend transport adapter (swap-in point)
- `src/lab/types.ts` — type definitions
- `src/lab/seed.ts` — deterministic seed graph
- `src/App.tsx` — main UI

## Scenarios

1. New Knowledge Ingest
2. Code Contradiction
3. Freshness Decay
4. Reconsolidation
5. Synaptic Tagging
6. Interference Management
7. Phasic vs Tonic Mode
8. Multi-Hop Retrieval
9. Project Memory Growth
10. Garbage Collection Audit
```

**Step 5: Update 3-code/CLAUDE.code.md with component entries**

**Step 6: Commit**

```bash
git add 3-code/
git commit -m "code: decompose into 3 components (core-engine, mcp-server, visual-test-lab)"
```

---

### Task 9: Copy Visual Test Lab Into Repo

**Files:**
- Create: `3-code/visual-test-lab/` — copy from extracted ZIP

**Step 1: Copy the visual test lab source**

```bash
cp -r /tmp/neuro-arch/src 3-code/visual-test-lab/src
cp /tmp/neuro-arch/package.json 3-code/visual-test-lab/
cp /tmp/neuro-arch/package-lock.json 3-code/visual-test-lab/
cp /tmp/neuro-arch/tsconfig.json 3-code/visual-test-lab/
cp /tmp/neuro-arch/vite.config.ts 3-code/visual-test-lab/
cp /tmp/neuro-arch/vitest.config.ts 3-code/visual-test-lab/
cp /tmp/neuro-arch/index.html 3-code/visual-test-lab/
cp /tmp/neuro-arch/README.md 3-code/visual-test-lab/
cp /tmp/neuro-arch/RUNBOOK.md 3-code/visual-test-lab/
```

**Step 2: Verify tests pass**

```bash
cd 3-code/visual-test-lab && npm install && npx vitest run
```

Expected: All tests pass.

**Step 3: Commit**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
git add 3-code/visual-test-lab/
git commit -m "feat: add visual test lab for neuro-MCP scenario testing"
```

---

### Task 10: Create Initial Decision Records

**Files:**
- Create: `decisions/DEC-code-wins-source-of-truth.md`
- Create: `decisions/DEC-code-wins-source-of-truth.history.md`
- Create: `decisions/DEC-two-stage-mutations.md`
- Create: `decisions/DEC-two-stage-mutations.history.md`

**Step 1: Read decision template**

```bash
cat decisions/_template.md
cat decisions/_template.history.md
```

**Step 2: Create DEC-code-wins-source-of-truth.md**

```markdown
# DEC-code-wins-source-of-truth

**Status:** Active
**Date:** 2026-04-10
**Trigger:** When reconcile detects brain vs code disagreement

## Decision

Code is always the source of truth when notes and code disagree. The reconcile function returns the contradiction and marks code as authoritative. Notes capture rationale, intent, and semantic memory; code captures current implementation state.

## Rationale

Notes can silently go stale. Code is always current (it either compiles/runs or it doesn't). Treating code as ground truth prevents the knowledge base from becoming a source of hallucination.

## Enforcement

- `reconcile.py` must set `source_of_truth: "code"` when disagreement is detected
- Search results from code always get `freshness: current` and `source_precision: 1.0`
- Brain notes that contradict code are marked with `contradiction_detected: true`
```

**Step 3: Create DEC-two-stage-mutations.md**

```markdown
# DEC-two-stage-mutations

**Status:** Active
**Date:** 2026-04-10
**Trigger:** When implementing any feature that modifies note content

## Decision

All mutations to note content follow a two-stage process:
1. **Auto-state transitions** — the system may change `status` in frontmatter (active → labile → stale → archived)
2. **Human-approved content mutation** — the system must not silently rewrite note body text; it may only draft suggestions

## Rationale

Trust is the product's foundation. Users must be confident that their written content is not silently altered. Status metadata is system-owned; content is human-owned.

## Enforcement

- `gc --apply` may change `status` field but must not alter note body
- Reconsolidation may set `status: labile` but must not rewrite note content
- `propose_note_patch` (future) creates a draft, not an in-place edit
```

**Step 4: Create corresponding .history.md files (initial entries)**

**Step 5: Commit**

```bash
git add decisions/
git commit -m "decisions: add foundational ADRs (code-wins, two-stage-mutations)"
```

---

### Task 11: Update Brain Note and Re-Index

**Files:**
- Modify: `/Users/benjaminpoersch/Obsidian_new/second-brain-starter-kit/04-projekte/neuro-mcp-server.md`

**Step 1: Update the brain note with SDLC status**

Add to the brain note:

```markdown
## SDLC Status (2026-04-10)

Project management via ai-scrum-scaffold:
- Phase: Specification (v2 extensions)
- 3 Goals defined: knowledge-discipline-engine, self-maintaining-memory, evidence-network
- 6 Requirements defined (all Must-have)
- 3 Constraints approved
- 3 Components: core-engine, mcp-server, visual-test-lab
- 2 ADRs: code-wins-source-of-truth, two-stage-mutations
- Next: `/SDLC-design` completeness assessment, then `/SDLC-implementation-plan`

## v2 Roadmap Priority

1. Reconsolidation Review Transactions (High, M)
2. Precision-Weighted Evidence Graph (High, L)
3. STC Promotion Queue + Monthly Homeostasis (High, M)
4. Interference Resolution Engine 2.0 (Medium, M)
5. Complementary Memory Ladder (Medium, L)
6. Global Coherence Auditor (Medium, L)
```

**Step 2: Update `last_verified` to today**

**Step 3: Re-index**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
uv run neuro-mcp --config config-self.yaml index
```

**Step 4: Commit the SDLC scaffold**

```bash
git add -A
git commit -m "feat: complete SDLC scaffold initialization with specs, design, components, and decisions"
```

---

### Task 12: Final Verification

**Step 1: Run all existing tests to confirm nothing broke**

```bash
cd /Users/benjaminpoersch/Obsidian_new/neuro_mcp/neuro_mcp_server_clean
uv run pytest -v
```

Expected: All tests pass (no regressions from scaffold addition).

**Step 2: Run SDLC-status skill to verify scaffold health**

Invoke `/SDLC-status` to see the project dashboard:
- Artifact counts per phase
- Task progress (none yet — that's expected)
- Phase-gate readiness
- Traceability health

**Step 3: Verify brain vault search returns updated context**

```bash
uv run neuro-mcp --config config-self.yaml search-brain "NeuroMCP SDLC"
```

Expected: The updated brain note appears with SDLC status.

---

## Summary

After all 12 tasks, the repo will have:

| Layer | Content |
|-------|---------|
| **1-spec** | 4 stakeholders, 3 goals, 3 constraints, 6 requirements |
| **2-design** | Architecture, data model, API design (populated from existing system + v2 vision) |
| **3-code** | 3 components (core-engine, mcp-server, visual-test-lab), task tracker ready |
| **4-deploy** | Runbook templates ready |
| **decisions** | 2 foundational ADRs |
| **skills** | 8 SDLC skills installed |
| **brain** | Updated project note with SDLC status and v2 roadmap |

Next step after this plan: run `/SDLC-implementation-plan` to generate the task backlog from the requirements, then execute tasks via `/SDLC-execute-next-task`.
