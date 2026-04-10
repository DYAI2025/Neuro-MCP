# Neuro-MCP Lab Runbook

## 1. Environment

- Node.js 20+
- npm 10+

## 2. Install

```bash
npm install
```

## 3. Start test lab

```bash
npm run dev
```

Open the local Vite URL and confirm all seven GUI regions are visible.

## 4. Execute deterministic scenario runs

1. Pick a scenario in Scenario Control Panel.
2. Click `Start`.
3. Click `Step` repeatedly to inspect intermediate transitions.
4. Use `Auto-play` for timed progression.
5. Observe changes in Graph, Timeline, Diff, and Metrics.
6. Use `Replay` to rerun the same scenario from seed baseline.
7. Use `Reset` to return to deterministic initial graph.

## 5. Query and retrieval verification

1. Enter a query in Query/Retrieval Panel.
2. Click `Run Retrieval`.
3. Validate ranked results and source-of-truth output.
4. Inspect retrieval path edges in the graph.

## 6. Add a new scenario

1. Open `src/lab/scenarios.ts`.
2. Register scenario via `registerScenario(...)`.
3. Define ordered steps and mutation handlers.
4. Emit timeline events for each state mutation.
5. Add tests in `src/lab/scenarios.test.ts` or new scenario-specific test file.

## 7. Integrate real Neuro-MCP backend

1. Keep engine and UI unchanged.
2. Replace adapter implementation in `src/lab/adapter.ts`.
3. Map backend events (SSE/WebSocket) to `TimelineEvent`.
4. Bind backend tool calls to scenario actions/query execution.
5. Preserve deterministic fixtures for CI through simulation fallback.

## 8. CI checks

```bash
npx vitest run
npm run build
```
