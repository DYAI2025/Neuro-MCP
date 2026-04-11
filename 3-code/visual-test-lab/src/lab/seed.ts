import type { KnowledgeEdge, KnowledgeNode, LabMetrics, LabState, RetrievalResult } from "./types";

const BASE_NODES: KnowledgeNode[] = [
  {
    id: "note-arch",
    label: "Architecture Overview",
    kind: "brain",
    status: "active",
    cluster: "brain",
    freshness: 0.92,
    precision: 0.88,
    linkedPaths: ["src/components/ExampleComponent.tsx"],
    contradiction: false,
    metadata: { decay_class: "90d", last_verified: "2026-04-10" },
  },
  {
    id: "note-stack",
    label: "Tech Stack Note",
    kind: "brain",
    status: "active",
    cluster: "brain",
    freshness: 0.84,
    precision: 0.8,
    linkedPaths: ["package.json"],
    contradiction: false,
    metadata: { claimed_dependencies: ["react", "prisma"], decay_class: "30d" },
  },
  {
    id: "note-inbox",
    label: "Inbox Idea",
    kind: "brain",
    status: "transient",
    cluster: "inbox",
    freshness: 0.7,
    precision: 0.35,
    linkedPaths: [],
    contradiction: false,
    metadata: { decay_class: "7d", created: "2026-04-10T09:00:00Z" },
  },
  {
    id: "code-package",
    label: "package.json",
    kind: "code",
    status: "source_of_truth",
    cluster: "code",
    freshness: 1,
    precision: 1,
    linkedPaths: ["package.json"],
    contradiction: false,
    metadata: { dependencies: ["react", "next"] },
  },
  {
    id: "code-ring",
    label: "ExampleComponent.tsx",
    kind: "code",
    status: "stable",
    cluster: "code",
    freshness: 1,
    precision: 1,
    linkedPaths: ["src/components/ExampleComponent.tsx"],
    contradiction: false,
    metadata: { language: "tsx" },
  },
  {
    id: "cluster-memory",
    label: "Project Memory Cluster",
    kind: "cluster",
    status: "stable",
    cluster: "meta",
    freshness: 0.86,
    precision: 0.9,
    linkedPaths: [],
    contradiction: false,
    metadata: { aggregate: true },
  },
];

const BASE_EDGES: KnowledgeEdge[] = [
  { id: "e1", source: "note-arch", target: "code-ring", kind: "verifies", weight: 0.9, label: "linked_path" },
  { id: "e2", source: "note-stack", target: "code-package", kind: "claim", weight: 0.7, label: "claims deps" },
  { id: "e3", source: "note-inbox", target: "cluster-memory", kind: "semantic", weight: 0.48, label: "transient signal" },
  { id: "e4", source: "note-arch", target: "cluster-memory", kind: "link", weight: 0.85, label: "belongs" },
  { id: "e5", source: "note-stack", target: "cluster-memory", kind: "link", weight: 0.78, label: "belongs" },
];

function baseMetrics(): LabMetrics {
  return {
    staleCount: 0,
    labileCount: 0,
    contradictionCount: 0,
    reindexEvents: 0,
    auditMode: "phasic",
  };
}

export function createSeedState(): LabState {
  return {
    nodes: structuredClone(BASE_NODES),
    edges: structuredClone(BASE_EDGES),
    timeline: [
      {
        id: "evt-boot",
        ts: Date.now(),
        type: "system.boot",
        message: "Seeded deterministic brain/code graph for Neuro-MCP lab.",
        payload: { nodes: BASE_NODES.length, edges: BASE_EDGES.length },
      },
    ],
    retrieval: [],
    selectedNodeId: null,
    selectedEdgeId: null,
    metrics: baseMetrics(),
    beforeScenario: null,
    lastDiff: null,
    activeScenarioId: null,
    pendingSteps: [],
    completedSteps: [],
  };
}

export function createRetrieval(query: string): RetrievalResult[] {
  const normalized = query.toLowerCase();
  const wantsCode = normalized.includes("code") || normalized.includes("dependency") || normalized.includes("react");
  return [
    {
      id: "r1",
      title: wantsCode ? "package.json dependencies" : "Tech Stack Note",
      kind: wantsCode ? "code" : "brain",
      relevance: 0.93,
      lexicalScore: 0.82,
      semanticScore: 0.95,
      sourceOfTruth: wantsCode ? "code" : "mixed",
      path: ["note-stack", "code-package", "cluster-memory"],
    },
    {
      id: "r2",
      title: "Architecture Overview",
      kind: "brain",
      relevance: 0.81,
      lexicalScore: 0.72,
      semanticScore: 0.84,
      sourceOfTruth: "brain",
      path: ["note-arch", "code-ring"],
    },
  ];
}
