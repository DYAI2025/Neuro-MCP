import type { RetrievalQueryResponse, TimelineEvent } from "./types";
import { ScenarioEngine } from "./engine";

export interface NeuroMcpLabAdapter {
  runScenario: (scenarioId: string) => void;
  stepScenario: () => void;
  autoplayScenario: () => void;
  stopAutoplay: () => void;
  reset: () => void;
  replay: () => void;
  runQuery: (query: string) => RetrievalQueryResponse;
  subscribeTimeline: (handler: (event: TimelineEvent) => void) => () => void;
}

// This adapter mirrors how a real backend bridge would be consumed.
// Swap with a WebSocket/SSE implementation without changing the React panels.
export function createSimulationAdapter(engine: ScenarioEngine): NeuroMcpLabAdapter {
  let lastEventId = "";

  return {
    runScenario: (scenarioId) => {
      engine.startScenario(scenarioId);
    },
    stepScenario: () => {
      engine.stepScenario();
    },
    autoplayScenario: () => {
      engine.autoplay();
    },
    stopAutoplay: () => {
      engine.stopAutoplay();
    },
    reset: () => {
      engine.reset();
    },
    replay: () => {
      engine.replay();
    },
    runQuery: (query) => engine.runQuery(query),
    subscribeTimeline: (handler) =>
      engine.subscribe((state) => {
        const next = state.timeline[0];
        if (!next || next.id === lastEventId) {
          return;
        }
        lastEventId = next.id;
        handler(next);
      }),
  };
}
