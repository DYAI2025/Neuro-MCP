import type {
  RegisteredScenario,
  ScenarioRuntime,
  ScenarioStep,
  ScenarioStepHandler,
} from "./types";

const registry = new Map<string, RegisteredScenario>();

function byId(runtime: ScenarioRuntime, nodeId: string) {
  return runtime.state.nodes.find((n) => n.id === nodeId);
}

function addStep(id: string, label: string, detail: string): ScenarioStep {
  return { id, label, detail };
}

function registerScenario(
  id: string,
  title: string,
  description: string,
  steps: ScenarioStep[],
  handlers: ScenarioStepHandler[]
) {
  registry.set(id, { id, title, description, steps, handlers });
}

registerScenario(
  "new-knowledge-ingest",
  "New Knowledge Ingest",
  "A new inbox note is ingested, indexed, linked, and visible in graph state.",
  [
    addStep("ingest-1", "Create note", "brain_ingest_note creates a new note under 80-inbox."),
    addStep("ingest-2", "Index and link", "Indexer generates semantic edge to architecture note."),
  ],
  [
    (runtime) => {
      runtime.state.nodes.push({
        id: "note-new-api",
        label: "API Discovery",
        kind: "brain",
        status: "transient",
        cluster: "inbox",
        freshness: 0.98,
        precision: 0.62,
        linkedPaths: ["src/api/client.ts"],
        contradiction: false,
        metadata: { decay_class: "7d", type: "inbox" },
      });
      runtime.emit({ type: "brain.ingest", message: "Created note 80-inbox/new-discovery.md" });
    },
    (runtime) => {
      runtime.state.edges.push({
        id: `e-ing-${runtime.state.edges.length}`,
        source: "note-new-api",
        target: "note-arch",
        kind: "semantic",
        weight: 0.73,
        label: "new relation",
      });
      runtime.state.metrics.reindexEvents += 1;
      runtime.emit({ type: "index.refresh", message: "Incremental refresh linked new note into memory graph." });
    },
  ]
);

registerScenario(
  "code-contradiction",
  "Code Contradiction",
  "A brain claim conflicts with manifest data and reconcile shifts source_of_truth to code.",
  [
    addStep("contra-1", "Inject mismatch", "Tech stack note still claims prisma while package manifest does not."),
    addStep("contra-2", "Reconcile", "Conflict edge is created and source_of_truth moves to code."),
  ],
  [
    (runtime) => {
      const note = byId(runtime, "note-stack");
      if (note) {
        note.contradiction = true;
        note.metadata.claimed_dependencies = ["react", "prisma"];
      }
      runtime.emit({ type: "reconcile.detect", message: "Detected dependency contradiction (prisma missing)." });
    },
    (runtime) => {
      runtime.state.edges.push({
        id: `e-conf-${runtime.state.edges.length}`,
        source: "note-stack",
        target: "code-package",
        kind: "conflict",
        weight: 1,
        label: "missing dependency",
      });
      runtime.state.metrics.contradictionCount += 1;
      const codeNode = byId(runtime, "code-package");
      if (codeNode) {
        codeNode.status = "source_of_truth";
      }
      runtime.emit({ type: "reconcile.result", message: "source_of_truth set to code for dependency claims." });
    },
  ]
);

registerScenario(
  "freshness-decay",
  "Freshness Decay",
  "Old verification dates cause freshness decay and stale/labile transitions.",
  [
    addStep("decay-1", "Advance clock", "last_verified age exceeds decay_class window."),
    addStep("decay-2", "Recompute freshness", "Affected note transitions to stale and labile."),
  ],
  [
    (runtime) => {
      const note = byId(runtime, "note-arch");
      if (note) {
        note.freshness = 0.34;
        note.metadata.last_verified = "2025-10-01";
      }
      runtime.emit({ type: "freshness.clock", message: "Simulated verification aging for architecture note." });
    },
    (runtime) => {
      const note = byId(runtime, "note-arch");
      if (note) {
        note.status = "stale";
      }
      runtime.state.metrics.staleCount += 1;
      runtime.state.metrics.labileCount += 1;
      runtime.emit({ type: "freshness.state", message: "Architecture note marked stale and queued for review." });
    },
  ]
);

registerScenario(
  "reconsolidation",
  "Reconsolidation",
  "Contradicted knowledge is marked labile instead of being overwritten.",
  [
    addStep("recon-1", "Mark labile", "Reconsolidation writes labile flags and reasons."),
    addStep("recon-2", "Create successor link", "A replacement note is linked while preserving history."),
  ],
  [
    (runtime) => {
      const note = byId(runtime, "note-stack");
      if (note) {
        note.status = "labile";
        note.metadata.labile_reasons = ["dependency mismatch"];
      }
      runtime.state.metrics.labileCount += 1;
      runtime.emit({ type: "reconsolidation.mark", message: "Tech Stack note marked labile with review reasons." });
    },
    (runtime) => {
      runtime.state.nodes.push({
        id: "note-stack-v2",
        label: "Tech Stack Note (v2)",
        kind: "brain",
        status: "active",
        cluster: "brain",
        freshness: 0.99,
        precision: 0.9,
        linkedPaths: ["package.json"],
        contradiction: false,
        metadata: { supersedes: "note-stack" },
      });
      runtime.state.edges.push({
        id: `e-recon-${runtime.state.edges.length}`,
        source: "note-stack-v2",
        target: "note-stack",
        kind: "link",
        weight: 1,
        label: "supersedes",
      });
      runtime.emit({ type: "reconsolidation.link", message: "Created successor note without deleting old memory." });
    },
  ]
);

registerScenario(
  "synaptic-tagging",
  "Synaptic Tagging",
  "An inbox note is promoted when correlated code changes occur inside STC window.",
  [
    addStep("st-1", "Detect overlap", "Changed files overlap linked_paths of transient inbox note."),
    addStep("st-2", "Promote note", "Decay class extends and status becomes stable."),
  ],
  [
    (runtime) => {
      const note = byId(runtime, "note-inbox");
      if (note) {
        note.linkedPaths = ["src/components/ExampleComponent.tsx"];
        note.metadata.stc_overlap = true;
      }
      runtime.emit({ type: "synaptic.detect", message: "Code change overlap detected for inbox note." });
    },
    (runtime) => {
      const note = byId(runtime, "note-inbox");
      if (note) {
        note.status = "stable";
        note.cluster = "brain";
        note.freshness = 0.95;
        note.metadata.decay_class = "30d";
      }
      runtime.emit({ type: "synaptic.promote", message: "Inbox note promoted to stable memory trace." });
    },
  ]
);

registerScenario(
  "interference-management",
  "Interference Management",
  "Highly similar notes produce merge, supersede, and cross-link actions.",
  [
    addStep("int-1", "Detect similarity", "Pair similarity exceeds threshold and enters candidate list."),
    addStep("int-2", "Apply strategy", "System proposes merge/cross-link and writes action edge."),
  ],
  [
    (runtime) => {
      runtime.emit({ type: "interference.detect", message: "Similarity score 0.91 found between stack notes." });
    },
    (runtime) => {
      if (!byId(runtime, "note-stack-v2")) {
        runtime.state.nodes.push({
          id: "note-stack-v2",
          label: "Tech Stack Note (v2)",
          kind: "brain",
          status: "active",
          cluster: "brain",
          freshness: 0.91,
          precision: 0.88,
          linkedPaths: ["package.json"],
          contradiction: false,
          metadata: { generated_by: "interference" },
        });
      }
      runtime.state.edges.push({
        id: `e-int-${runtime.state.edges.length}`,
        source: "note-stack",
        target: "note-stack-v2",
        kind: "semantic",
        weight: 0.91,
        label: "merge_candidate",
      });
      runtime.emit({ type: "interference.action", message: "Action proposed: merge/supersede relationship." });
    },
  ]
);

registerScenario(
  "phasic-vs-tonic",
  "Phasic vs Tonic Audits",
  "Small change sets keep phasic mode while larger updates trigger tonic full-audit.",
  [
    addStep("mode-1", "Phasic pass", "Small change set keeps incremental audit mode."),
    addStep("mode-2", "Tonic switch", "Large change set triggers full reconcile mode."),
  ],
  [
    (runtime) => {
      runtime.state.metrics.auditMode = "phasic";
      runtime.emit({ type: "audit.mode", message: "Phasic mode active for small change set." });
    },
    (runtime) => {
      runtime.state.metrics.auditMode = "tonic";
      runtime.state.metrics.reindexEvents += 1;
      runtime.emit({ type: "audit.mode", message: "Switched to tonic full-reconcile due to large delta." });
    },
  ]
);

registerScenario(
  "multi-hop-retrieval",
  "Multi-Hop Retrieval",
  "A query traverses multiple nodes to assemble final answer evidence path.",
  [
    addStep("hop-1", "Run query", "Search traverses note -> manifest -> code chunk."),
    addStep("hop-2", "Persist path", "Retrieval path edges are added for observability."),
  ],
  [
    (runtime) => {
      runtime.emit({ type: "retrieval.query", message: "Query traversed 3 nodes with mixed evidence." });
    },
    (runtime) => {
      runtime.state.edges.push({
        id: `e-hop-${runtime.state.edges.length}`,
        source: "note-stack",
        target: "code-package",
        kind: "retrieval_path",
        weight: 0.88,
        label: "hop 1",
      });
      runtime.state.edges.push({
        id: `e-hop-${runtime.state.edges.length}`,
        source: "code-package",
        target: "code-ring",
        kind: "retrieval_path",
        weight: 0.84,
        label: "hop 2",
      });
      runtime.emit({ type: "retrieval.path", message: "Stored retrieval path for replay and inspection." });
    },
  ]
);

registerScenario(
  "project-memory-growth",
  "Project Memory Growth",
  "New knowledge shifts cluster priorities and rebalances memory graph.",
  [
    addStep("growth-1", "Attach new domain", "Add product-domain cluster and memory note."),
    addStep("growth-2", "Reprioritize", "Cluster weights and semantic links shift."),
  ],
  [
    (runtime) => {
      runtime.state.nodes.push({
        id: "cluster-product",
        label: "Product Intent Cluster",
        kind: "cluster",
        status: "stable",
        cluster: "meta",
        freshness: 0.97,
        precision: 0.91,
        linkedPaths: [],
        contradiction: false,
        metadata: { priority: "high" },
      });
      runtime.emit({ type: "memory.expand", message: "Added new product memory cluster." });
    },
    (runtime) => {
      runtime.state.edges.push({
        id: `e-growth-${runtime.state.edges.length}`,
        source: "cluster-product",
        target: "cluster-memory",
        kind: "link",
        weight: 0.8,
        label: "priority_shift",
      });
      runtime.emit({ type: "memory.rebalance", message: "Priority rebalance completed across clusters." });
    },
  ]
);

registerScenario(
  "garbage-collection-audit",
  "Garbage Collection Audit",
  "Only archive candidates are flagged; no destructive delete is performed.",
  [
    addStep("gc-1", "Flag candidates", "GC scan flags notes with stale+low precision."),
    addStep("gc-2", "Audit output", "Archive candidates are exposed in timeline and metadata."),
  ],
  [
    (runtime) => {
      const note = byId(runtime, "note-arch");
      if (note) {
        note.metadata.gc_candidate = true;
      }
      runtime.emit({ type: "gc.scan", message: "GC dry-run identified archive candidate(s)." });
    },
    (runtime) => {
      runtime.emit({
        type: "gc.audit",
        message: "Dry-run complete. 1 candidate; 0 deletions.",
        payload: { dry_run: true, candidates: ["note-arch"] },
      });
    },
  ]
);

export function listScenarios(): RegisteredScenario[] {
  return [...registry.values()];
}

export function getScenarioById(id: string): RegisteredScenario | undefined {
  return registry.get(id);
}
