import { createRetrieval, createSeedState } from "./seed";
import { getScenarioById, listScenarios } from "./scenarios";
import type {
  DiffSnapshot,
  LabMetrics,
  LabState,
  RetrievalQueryResponse,
  TimelineEvent,
} from "./types";

type Subscriber = (state: LabState) => void;

function cloneMetrics(metrics: LabMetrics): LabMetrics {
  return {
    staleCount: metrics.staleCount,
    labileCount: metrics.labileCount,
    contradictionCount: metrics.contradictionCount,
    reindexEvents: metrics.reindexEvents,
    auditMode: metrics.auditMode,
  };
}

function buildDiff(state: LabState): DiffSnapshot | null {
  const baseline = state.beforeScenario;
  if (!baseline) {
    return null;
  }

  const beforeNodeMap = new Map(baseline.nodes.map((n) => [n.id, n]));
  const changedNodes = state.nodes
    .filter((node) => JSON.stringify(node) !== JSON.stringify(beforeNodeMap.get(node.id)))
    .map((node) => node.id);

  const beforeEdgeMap = new Map(baseline.edges.map((e) => [e.id, e]));
  const changedEdges = state.edges
    .filter((edge) => JSON.stringify(edge) !== JSON.stringify(beforeEdgeMap.get(edge.id)))
    .map((edge) => edge.id);

  return {
    changedNodes,
    changedEdges,
    beforeMetrics: cloneMetrics(baseline.metrics),
    afterMetrics: cloneMetrics(state.metrics),
  };
}

export class ScenarioEngine {
  private state: LabState;
  private subscribers = new Set<Subscriber>();
  private idCounter = 0;
  private autoplayTimer: number | null = null;

  constructor() {
    this.state = createSeedState();
  }

  getState() {
    return this.state;
  }

  subscribe(subscriber: Subscriber) {
    this.subscribers.add(subscriber);
    subscriber(this.state);
    return () => {
      this.subscribers.delete(subscriber);
    };
  }

  private notify() {
    for (const subscriber of this.subscribers) {
      subscriber(this.state);
    }
  }

  private emit(event: Omit<TimelineEvent, "id" | "ts">) {
    const timelineEvent: TimelineEvent = {
      ...event,
      id: `evt-${this.idCounter++}`,
      ts: Date.now(),
    };
    this.state.timeline = [timelineEvent, ...this.state.timeline].slice(0, 150);
    this.notify();
  }

  reset() {
    this.stopAutoplay();
    this.state = createSeedState();
    this.notify();
  }

  replay() {
    const scenarioId = this.state.activeScenarioId;
    this.reset();
    if (scenarioId) {
      this.startScenario(scenarioId);
      this.runAllSteps();
    }
  }

  selectNode(nodeId: string | null) {
    this.state.selectedNodeId = nodeId;
    this.state.selectedEdgeId = null;
    this.notify();
  }

  selectEdge(edgeId: string | null) {
    this.state.selectedEdgeId = edgeId;
    this.state.selectedNodeId = null;
    this.notify();
  }

  startScenario(scenarioId: string) {
    const scenario = getScenarioById(scenarioId);
    if (!scenario) {
      return;
    }

    this.stopAutoplay();
    this.state.activeScenarioId = scenarioId;
    this.state.pendingSteps = [...scenario.steps];
    this.state.completedSteps = [];
    this.state.beforeScenario = {
      nodes: structuredClone(this.state.nodes),
      edges: structuredClone(this.state.edges),
      metrics: cloneMetrics(this.state.metrics),
    };
    this.state.lastDiff = null;
    this.emit({ type: "scenario.start", message: `Started scenario: ${scenario.title}`, scenarioId });
  }

  stepScenario() {
    const scenarioId = this.state.activeScenarioId;
    if (!scenarioId) {
      return;
    }
    const scenario = getScenarioById(scenarioId);
    if (!scenario || this.state.pendingSteps.length === 0) {
      this.finishScenario();
      return;
    }

    const completedCount = this.state.completedSteps.length;
    const step = this.state.pendingSteps.shift();
    const handler = scenario.handlers[completedCount];
    if (!step || !handler) {
      this.finishScenario();
      return;
    }

    handler({ state: this.state, emit: (evt) => this.emit({ ...evt, scenarioId }) });
    this.state.completedSteps.push(step);
    this.state.lastDiff = buildDiff(this.state);
    this.emit({
      type: "scenario.step",
      message: `${step.label}: ${step.detail}`,
      scenarioId,
      payload: { stepId: step.id },
    });

    if (this.state.pendingSteps.length === 0) {
      this.finishScenario();
    }
  }

  runAllSteps() {
    while (this.state.activeScenarioId && this.state.pendingSteps.length > 0) {
      this.stepScenario();
    }
  }

  autoplay(delayMs = 900) {
    this.stopAutoplay();
    this.autoplayTimer = window.setInterval(() => {
      if (!this.state.activeScenarioId || this.state.pendingSteps.length === 0) {
        this.stopAutoplay();
        return;
      }
      this.stepScenario();
    }, delayMs);
  }

  stopAutoplay() {
    if (this.autoplayTimer !== null) {
      window.clearInterval(this.autoplayTimer);
      this.autoplayTimer = null;
    }
  }

  runQuery(query: string): RetrievalQueryResponse {
    const results = createRetrieval(query);
    this.state.retrieval = results;
    this.state.nodes = this.state.nodes.filter((node) => !node.id.startsWith("query-result-"));
    this.state.edges = this.state.edges.filter((edge) => !edge.id.startsWith("query-edge-"));
    for (const [index, result] of results.entries()) {
      this.state.nodes.push({
        id: `query-result-${index}`,
        label: result.title,
        kind: "retrieval",
        status: "active",
        cluster: "query",
        freshness: result.relevance,
        precision: result.semanticScore,
        linkedPaths: [],
        contradiction: result.sourceOfTruth === "code",
        metadata: { query },
      });
      this.state.edges.push({
        id: `query-edge-${index}`,
        source: result.path[0] ?? "note-stack",
        target: `query-result-${index}`,
        kind: "retrieval_path",
        weight: result.relevance,
        label: "retrieval",
      });
    }

    const sourceOfTruth: "brain" | "code" | "mixed" = results.some((r) => r.sourceOfTruth === "code")
      ? "code"
      : "mixed";

    this.emit({
      type: "query.run",
      message: `Executed retrieval query: ${query}`,
      payload: { sourceOfTruth, resultCount: results.length },
    });
    return { query, results, sourceOfTruth };
  }

  availableScenarios() {
    return listScenarios();
  }

  private finishScenario() {
    if (!this.state.activeScenarioId) {
      return;
    }
    this.state.lastDiff = buildDiff(this.state);
    const scenarioId = this.state.activeScenarioId;
    this.emit({ type: "scenario.finish", message: "Scenario completed.", scenarioId });
  }
}
