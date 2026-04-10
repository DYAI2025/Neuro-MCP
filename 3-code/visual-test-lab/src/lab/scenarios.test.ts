import { describe, expect, it } from "vitest";

import { listScenarios } from "./scenarios";

describe("scenario registry", () => {
  it("contains required ten minimum scenarios", () => {
    const ids = listScenarios().map((scenario) => scenario.id);
    expect(ids.length).toBeGreaterThanOrEqual(10);
    expect(ids).toContain("new-knowledge-ingest");
    expect(ids).toContain("code-contradiction");
    expect(ids).toContain("freshness-decay");
    expect(ids).toContain("reconsolidation");
    expect(ids).toContain("synaptic-tagging");
    expect(ids).toContain("interference-management");
    expect(ids).toContain("phasic-vs-tonic");
    expect(ids).toContain("multi-hop-retrieval");
    expect(ids).toContain("project-memory-growth");
    expect(ids).toContain("garbage-collection-audit");
  });
});
