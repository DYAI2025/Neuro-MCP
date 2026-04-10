import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("react-cytoscapejs", () => ({
  default: () => <div data-testid="cytoscape-mock" />,
}));

import App from "./App";

describe("App", () => {
  it("renders the test lab panels", () => {
    render(<App />);
    expect(screen.getByText(/Neuro-MCP Visual Test Environment Kit/i)).toBeInTheDocument();
    expect(screen.getByText(/Graph View/i)).toBeInTheDocument();
    expect(screen.getByText(/Scenario Control Panel/i)).toBeInTheDocument();
    expect(screen.getByText(/Event Timeline/i)).toBeInTheDocument();
    expect(screen.getByText(/Inspector Panel/i)).toBeInTheDocument();
    expect(screen.getByText(/System Health \/ Metrics Panel/i)).toBeInTheDocument();
  });
});
