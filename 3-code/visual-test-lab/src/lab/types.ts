export type NodeKind = "brain" | "code" | "cluster" | "query" | "retrieval";

export type NodeStatus =
  | "active"
  | "labile"
  | "stale"
  | "source_of_truth"
  | "transient"
  | "stable";

export type EdgeKind = "link" | "claim" | "conflict" | "semantic" | "retrieval_path" | "verifies";

export type AuditMode = "phasic" | "tonic";

export interface KnowledgeNode {
  id: string;
  label: string;
  kind: NodeKind;
  status: NodeStatus;
  cluster: string;
  freshness: number;
  precision: number;
  linkedPaths: string[];
  contradiction: boolean;
  metadata: Record<string, string | number | boolean | string[]>;
}

export interface KnowledgeEdge {
  id: string;
  source: string;
  target: string;
  kind: EdgeKind;
  weight: number;
  label: string;
}

export interface RetrievalResult {
  id: string;
  title: string;
  kind: NodeKind;
  relevance: number;
  lexicalScore: number;
  semanticScore: number;
  sourceOfTruth: "brain" | "code" | "mixed";
  path: string[];
}

export interface ScenarioStep {
  id: string;
  label: string;
  detail: string;
}

export interface ScenarioDefinition {
  id: string;
  title: string;
  description: string;
  steps: ScenarioStep[];
}

export interface TimelineEvent {
  id: string;
  ts: number;
  type: string;
  message: string;
  scenarioId?: string;
  payload?: Record<string, unknown>;
}

export interface LabMetrics {
  staleCount: number;
  labileCount: number;
  contradictionCount: number;
  reindexEvents: number;
  auditMode: AuditMode;
}

export interface DiffSnapshot {
  changedNodes: string[];
  changedEdges: string[];
  beforeMetrics: LabMetrics;
  afterMetrics: LabMetrics;
}

export interface LabState {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  timeline: TimelineEvent[];
  retrieval: RetrievalResult[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  metrics: LabMetrics;
  beforeScenario: { nodes: KnowledgeNode[]; edges: KnowledgeEdge[]; metrics: LabMetrics } | null;
  lastDiff: DiffSnapshot | null;
  activeScenarioId: string | null;
  pendingSteps: ScenarioStep[];
  completedSteps: ScenarioStep[];
}

export interface ScenarioRuntime {
  state: LabState;
  emit: (event: Omit<TimelineEvent, "id" | "ts">) => void;
}

export type ScenarioStepHandler = (runtime: ScenarioRuntime) => void;

export interface RegisteredScenario extends ScenarioDefinition {
  handlers: ScenarioStepHandler[];
}

export interface RetrievalQueryResponse {
  query: string;
  results: RetrievalResult[];
  sourceOfTruth: "brain" | "code" | "mixed";
}
