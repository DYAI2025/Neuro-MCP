import { useEffect, useMemo, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import { motion } from "framer-motion";
import type cytoscape from "cytoscape";

import { createSimulationAdapter } from "./lab/adapter";
import { ScenarioEngine } from "./lab/engine";
import type { KnowledgeEdge, KnowledgeNode, LabState, TimelineEvent } from "./lab/types";

const engine = new ScenarioEngine();
const adapter = createSimulationAdapter(engine);

const statusClass: Record<KnowledgeNode["status"], string> = {
  active: "bg-emerald-500",
  labile: "bg-amber-500",
  stale: "bg-rose-500",
  source_of_truth: "bg-blue-500",
  transient: "bg-violet-500",
  stable: "bg-cyan-500",
};

function edgeColor(kind: KnowledgeEdge["kind"]) {
  if (kind === "conflict") return "#f43f5e";
  if (kind === "retrieval_path") return "#22c55e";
  if (kind === "semantic") return "#a855f7";
  return "#64748b";
}

export default function App() {
  const [state, setState] = useState<LabState>(engine.getState());
  const [query, setQuery] = useState("Are we using prisma in production?");
  const [selectedScenario, setSelectedScenario] = useState(engine.availableScenarios()[0]?.id ?? "");
  const [latestEvent, setLatestEvent] = useState<TimelineEvent | null>(null);

  useEffect(() => {
    const unsubscribeState = engine.subscribe(setState);
    const unsubscribeTimeline = adapter.subscribeTimeline(setLatestEvent);
    return () => {
      unsubscribeState();
      unsubscribeTimeline();
    };
  }, []);

  const selectedNode = useMemo(
    () => state.nodes.find((node) => node.id === state.selectedNodeId) ?? null,
    [state.nodes, state.selectedNodeId]
  );

  const selectedEdge = useMemo(
    () => state.edges.find((edge) => edge.id === state.selectedEdgeId) ?? null,
    [state.edges, state.selectedEdgeId]
  );

  const graphElements = useMemo(() => {
    const nodes = state.nodes.map((node) => ({ data: { id: node.id, label: node.label, kind: node.kind, status: node.status } }));
    const edges = state.edges.map((edge) => ({
      data: { id: edge.id, source: edge.source, target: edge.target, label: edge.label, kind: edge.kind, weight: edge.weight },
    }));
    return [...nodes, ...edges];
  }, [state.nodes, state.edges]);

  const scenarios = engine.availableScenarios();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <motion.header
        initial={{ opacity: 0, y: -14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="border-b border-slate-800 px-6 py-4"
      >
        <h1 className="text-2xl font-semibold tracking-tight">Neuro-MCP Visual Test Environment Kit</h1>
        <p className="mt-1 text-sm text-slate-400">
          Deterministic scenario lab for brain vs code reconciliation, freshness, reconsolidation, interference and audit dynamics.
        </p>
      </motion.header>

      <main className="grid grid-cols-12 gap-4 p-4">
        <section className="col-span-12 lg:col-span-8 border border-slate-800 bg-slate-900/40">
          <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Graph View</h2>
            <span className="text-xs text-slate-400">Obsidian-style knowledge map</span>
          </div>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }} className="h-[420px]">
            <CytoscapeComponent
              elements={graphElements}
              style={{ width: "100%", height: "100%" }}
              cy={(cy: cytoscape.Core) => {
                cy.on("tap", "node", (event: cytoscape.EventObject) => {
                  adapter.stopAutoplay();
                  engine.selectNode(event.target.id());
                });
                cy.on("tap", "edge", (event: cytoscape.EventObject) => {
                  adapter.stopAutoplay();
                  engine.selectEdge(event.target.id());
                });
              }}
              stylesheet={[
                {
                  selector: "node",
                  style: {
                    label: "data(label)",
                    color: "#e2e8f0",
                    "font-size": "10",
                    "text-wrap": "wrap",
                    "text-max-width": "90",
                    "background-color": "#334155",
                    width: "28",
                    height: "28",
                  },
                },
                {
                  selector: "edge",
                  style: {
                    width: "2",
                    "line-color": "#64748b",
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle",
                    "target-arrow-color": "#64748b",
                    label: "data(label)",
                    "font-size": "8",
                    color: "#94a3b8",
                  },
                },
                {
                  selector: "node[status = 'source_of_truth']",
                  style: { "background-color": "#3b82f6", width: "36", height: "36" },
                },
                { selector: "node[status = 'stale']", style: { "background-color": "#ef4444" } },
                { selector: "node[status = 'labile']", style: { "background-color": "#f59e0b" } },
                { selector: "node[status = 'transient']", style: { "background-color": "#8b5cf6" } },
                {
                  selector: "edge[kind = 'conflict']",
                  style: { "line-color": "#f43f5e", "target-arrow-color": "#f43f5e", width: "3" },
                },
                { selector: "edge[kind = 'retrieval_path']", style: { "line-color": "#22c55e", "target-arrow-color": "#22c55e" } },
              ]}
              layout={{ name: "cose", fit: true, padding: 30, animate: false }}
            />
          </motion.div>
        </section>

        <section className="col-span-12 lg:col-span-4 border border-slate-800 bg-slate-900/40">
          <div className="border-b border-slate-800 px-3 py-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Scenario Control Panel</h2>
          </div>
          <div className="space-y-3 p-3 text-sm">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-slate-400">Scenario</span>
              <select
                value={selectedScenario}
                onChange={(event) => setSelectedScenario(event.target.value)}
                className="border border-slate-700 bg-slate-950 px-2 py-2"
              >
                {scenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.title}
                  </option>
                ))}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button className="border border-cyan-700 px-2 py-2 hover:bg-cyan-900/30" onClick={() => adapter.runScenario(selectedScenario)}>
                Start
              </button>
              <button className="border border-violet-700 px-2 py-2 hover:bg-violet-900/30" onClick={() => adapter.stepScenario()}>
                Step
              </button>
              <button className="border border-emerald-700 px-2 py-2 hover:bg-emerald-900/30" onClick={() => adapter.autoplayScenario()}>
                Auto-play
              </button>
              <button className="border border-amber-700 px-2 py-2 hover:bg-amber-900/30" onClick={() => adapter.stopAutoplay()}>
                Stop
              </button>
              <button className="border border-slate-600 px-2 py-2 hover:bg-slate-800" onClick={() => adapter.replay()}>
                Replay
              </button>
              <button className="border border-rose-700 px-2 py-2 hover:bg-rose-900/30" onClick={() => adapter.reset()}>
                Reset
              </button>
            </div>
            <p className="text-xs text-slate-400">Completed steps: {state.completedSteps.length} | Pending: {state.pendingSteps.length}</p>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-4 border border-slate-800 bg-slate-900/40">
          <div className="border-b border-slate-800 px-3 py-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Event Timeline</h2>
          </div>
          <motion.ul layout className="h-[280px] overflow-auto p-3 text-xs">
            {state.timeline.map((event) => (
              <motion.li
                key={event.id}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                className="mb-2 border-l border-slate-700 pl-2"
              >
                <p className="text-slate-400">{new Date(event.ts).toLocaleTimeString()} | {event.type}</p>
                <p>{event.message}</p>
              </motion.li>
            ))}
          </motion.ul>
        </section>

        <section className="col-span-12 lg:col-span-4 border border-slate-800 bg-slate-900/40">
          <div className="border-b border-slate-800 px-3 py-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Inspector Panel</h2>
          </div>
          <div className="space-y-2 p-3 text-xs">
            {selectedNode ? (
              <>
                <h3 className="font-semibold">{selectedNode.label}</h3>
                <p>Kind: {selectedNode.kind}</p>
                <p className="flex items-center gap-2">Status <span className={`inline-block h-2.5 w-2.5 ${statusClass[selectedNode.status]}`} /> {selectedNode.status}</p>
                <p>Freshness: {(selectedNode.freshness * 100).toFixed(0)}%</p>
                <p>Precision: {(selectedNode.precision * 100).toFixed(0)}%</p>
                <p>Linked paths: {selectedNode.linkedPaths.join(", ") || "none"}</p>
                <p>Contradiction: {String(selectedNode.contradiction)}</p>
              </>
            ) : selectedEdge ? (
              <>
                <h3 className="font-semibold">{selectedEdge.label}</h3>
                <p>Kind: {selectedEdge.kind}</p>
                <p>Weight: {selectedEdge.weight.toFixed(2)}</p>
                <p>Source: {selectedEdge.source}</p>
                <p>Target: {selectedEdge.target}</p>
                <p style={{ color: edgeColor(selectedEdge.kind) }}>Visual cue: {selectedEdge.kind}</p>
              </>
            ) : (
              <p className="text-slate-400">Select a node or edge in graph view.</p>
            )}
          </div>
        </section>

        <section className="col-span-12 lg:col-span-4 border border-slate-800 bg-slate-900/40">
          <div className="border-b border-slate-800 px-3 py-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Diff / Before-After Panel</h2>
          </div>
          <div className="space-y-2 p-3 text-xs">
            {state.lastDiff ? (
              <>
                <p>Changed nodes: {state.lastDiff.changedNodes.length}</p>
                <p>Changed edges: {state.lastDiff.changedEdges.length}</p>
                <p>Stale: {state.lastDiff.beforeMetrics.staleCount}{" -> "}{state.lastDiff.afterMetrics.staleCount}</p>
                <p>Labile: {state.lastDiff.beforeMetrics.labileCount}{" -> "}{state.lastDiff.afterMetrics.labileCount}</p>
                <p>Contradictions: {state.lastDiff.beforeMetrics.contradictionCount}{" -> "}{state.lastDiff.afterMetrics.contradictionCount}</p>
              </>
            ) : (
              <p className="text-slate-400">Run a scenario to generate deterministic before/after diff.</p>
            )}
          </div>
        </section>

        <section className="col-span-12 lg:col-span-4 border border-slate-800 bg-slate-900/40">
          <div className="border-b border-slate-800 px-3 py-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Query / Retrieval Panel</h2>
          </div>
          <div className="space-y-2 p-3 text-xs">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-16 w-full border border-slate-700 bg-slate-950 p-2"
            />
            <button className="border border-emerald-700 px-2 py-2 hover:bg-emerald-900/30" onClick={() => adapter.runQuery(query)}>
              Run Retrieval
            </button>
            <p className="text-slate-400">Latest event: {latestEvent?.message ?? "none"}</p>
            <ul className="space-y-1">
              {state.retrieval.map((result) => (
                <li key={result.id} className="border-l border-slate-700 pl-2">
                  {result.title} ({result.kind}) | rel={result.relevance.toFixed(2)} | source={result.sourceOfTruth}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="col-span-12 border border-slate-800 bg-slate-900/40">
          <div className="border-b border-slate-800 px-3 py-2">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">System Health / Metrics Panel</h2>
          </div>
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="grid grid-cols-2 gap-4 px-3 py-3 text-xs lg:grid-cols-5"
          >
            <p>Stale count: <span className="font-semibold">{state.metrics.staleCount}</span></p>
            <p>Labile count: <span className="font-semibold">{state.metrics.labileCount}</span></p>
            <p>Contradiction count: <span className="font-semibold">{state.metrics.contradictionCount}</span></p>
            <p>Reindex events: <span className="font-semibold">{state.metrics.reindexEvents}</span></p>
            <p>Audit mode: <span className="font-semibold uppercase">{state.metrics.auditMode}</span></p>
          </motion.div>
        </section>
      </main>
    </div>
  );
}
