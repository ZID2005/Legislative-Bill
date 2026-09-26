/**
 * __tests__/components/StatePredictionFirewall.test.tsx
 * ======================================================
 * Tests for the State Prediction Firewall component.
 *
 * CRITICAL: Verifies that prediction-related content is NEVER shown.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";

describe("StatePredictionFirewall", () => {
  it("renders without crashing", () => {
    const { container } = render(<StatePredictionFirewall state="Kerala" />);
    expect(container).toBeTruthy();
  });

  it("shows the firewall heading", () => {
    render(<StatePredictionFirewall state="Kerala" />);
    expect(
      screen.getByText(/market prediction is not currently available for state legislation/i)
    ).toBeInTheDocument();
  });

  it("shows the state name", () => {
    render(<StatePredictionFirewall state="Telangana" />);
    expect(screen.getByText(/Telangana/i)).toBeInTheDocument();
  });

  it("shows available capabilities", () => {
    render(<StatePredictionFirewall state="Karnataka" />);
    expect(screen.getAllByText(/Legislative Intelligence/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Economic Impact/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Corporate Exposure/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Market Relevance/i)).toBeInTheDocument();
  });

  it("explicitly lists what is NOT available", () => {
    render(<StatePredictionFirewall state="Andhra Pradesh" />);
    // These must appear in the 'not available' list
    expect(screen.getByText(/Predicted stock return/i)).toBeInTheDocument();
    expect(screen.getByText(/Market direction prediction/i)).toBeInTheDocument();
    expect(screen.getByText(/Buy \/ Sell \/ Hold signal/i)).toBeInTheDocument();
    expect(screen.getByText(/Confidence score/i)).toBeInTheDocument();
  });

  it("does NOT show prediction numbers or values", () => {
    // Must not show actual quantitative prediction numbers, gauges, or targets
    expect(screen.queryByText(/[+-]\d+(\.\d+)?%/)).not.toBeInTheDocument();
    expect(screen.queryByText(/NIFTY 50 Impact/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/BSE SENSEX Target/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Confidence: \d+%/i)).not.toBeInTheDocument();
  });

  it("has accessible section role", () => {
    render(<StatePredictionFirewall state="Kerala" />);
    const section = screen.getByRole("region", { name: /state prediction status/i });
    expect(section).toBeInTheDocument();
  });

  it("displays backend message when provided", () => {
    const predStatus = {
      available: false,
      has_predictions: false,
      bill_id: "test-bill",
      message: "State legislation firewall active.",
      jurisdiction: "state",
      predictions: [],
      items: [],
      total: 0,
    };
    render(<StatePredictionFirewall state="Kerala" predictionStatus={predStatus} />);
    expect(screen.getByText(/State legislation firewall active/i)).toBeInTheDocument();
  });
});
