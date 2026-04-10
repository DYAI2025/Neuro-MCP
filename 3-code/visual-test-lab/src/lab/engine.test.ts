import { describe, expect, it } from "vitest";
import { ScenarioEngine } from "./engine";

describe("ScenarioEngine", () => {
  it("runs scenario steps deterministically", () => {
    const engine = new ScenarioEngine();
    engine.startScenario("code-contradiction");
    engine.stepScenario();
    engine.stepScenario();

    const state = engine.getState();
    const stackNote = state.nodes.find((node) => node.id === "note-stack");
    expect(stackNote?.contradiction).toBe(true);
    expect(state.metrics.contradictionCount).toBe(1);
    expect(state.timeline[0].type).toBe("scenario.finish");
  });

  it("resets to seed state", () => {
    const engine = new ScenarioEngine();
    engine.startScenario("freshness-decay");
    engine.runAllSteps();
    expect(engine.getState().metrics.staleCount).toBeGreaterThan(0);
    engine.reset();
    expect(engine.getState().metrics.staleCount).toBe(0);
    expect(engine.getState().nodes.find((node) => node.id === "note-arch")?.status).toBe("active");
  });
});
