# Neuro-MCP Visual Test Environment Kit

Production-oriented visual test lab for Neuro-MCP knowledge behavior. This kit provides a deterministic, replayable GUI where engineering teams can trigger scenarios and inspect how brain/code memory states evolve.

## What this kit provides

- Obsidian-like graph view with typed nodes and edges
- Scenario control with start, step, autoplay, stop, replay, reset
- Realtime event timeline of internal operations
- Inspector panel for selected node/edge diagnostics
- Before/after diff panel after each scenario run
- Query and retrieval panel with source-of-truth visibility
- Health and metrics panel for stale/labile/contradiction/audit mode
- Plugin-like scenario registry (10 baseline scenarios included)
- Deterministic seed graph and reproducible flow execution
- Automated tests for scenario engine and UI skeleton

## Integration status

ASSUMPTION: This repository currently runs as a React/Vite frontend package.

- Implemented now: a simulation adapter that mirrors Neuro-MCP tool semantics and event flow.
- Swap-in point: `src/lab/adapter.ts` for SSE/WebSocket backend transport.
- Core engine + state model are transport-agnostic and ready for backend wiring.

## Required scenarios included

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

## Start

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Tests

```bash
npx vitest run
```

## Runbook

Detailed operator runbook is in `RUNBOOK.md`.
