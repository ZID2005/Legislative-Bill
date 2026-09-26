/**
 * __tests__/components/CapabilityBadge.test.tsx
 * ===============================================
 * Tests for CapabilityBadge, JurisdictionBadge, PredictionAvailability,
 * MarketRelevanceBadge, and CorporateExposureBadge.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  CapabilityBadge,
  JurisdictionBadge,
  PredictionAvailability,
  MarketRelevanceBadge,
  CorporateExposureBadge,
  CoverageStatus,
} from "@/components/coverage/CapabilityBadge";

describe("CapabilityBadge", () => {
  it("renders Level 1 — Market Modelled", () => {
    render(<CapabilityBadge level={1} />);
    expect(screen.getByText(/L1 · Market Modelled/i)).toBeInTheDocument();
  });

  it("renders Level 2 — Legislative Intelligence", () => {
    render(<CapabilityBadge level={2} />);
    expect(screen.getByText(/L2 · Legislative Intelligence/i)).toBeInTheDocument();
  });

  it("renders Level 3 — Planned Coverage", () => {
    render(<CapabilityBadge level={3} />);
    expect(screen.getByText(/L3 · Planned Coverage/i)).toBeInTheDocument();
  });

  it("has accessible aria-label for Level 1", () => {
    render(<CapabilityBadge level={1} />);
    expect(screen.getByLabelText(/Coverage: Market Modelled/i)).toBeInTheDocument();
  });

  it("shows tooltip sublabel when showTooltip=true", () => {
    render(<CapabilityBadge level={1} showTooltip />);
    const badge = screen.getByLabelText(/Coverage: Market Modelled/i);
    expect(badge.getAttribute("title")).toContain("Quantitative predictions available");
  });

  it("does NOT show tooltip when showTooltip=false (default)", () => {
    render(<CapabilityBadge level={2} />);
    const badge = screen.getByLabelText(/Coverage: Legislative Intelligence/i);
    expect(badge.getAttribute("title")).toBeNull();
  });
});

describe("JurisdictionBadge", () => {
  it("renders Central Parliament for central jurisdiction", () => {
    render(<JurisdictionBadge jurisdiction="central" />);
    expect(screen.getByText("Central Parliament")).toBeInTheDocument();
  });

  it("renders State Assembly with state name for state jurisdiction", () => {
    render(<JurisdictionBadge jurisdiction="state" state="Karnataka" />);
    expect(screen.getByText("Karnataka Assembly")).toBeInTheDocument();
  });

  it("renders generic State Assembly when state is omitted", () => {
    render(<JurisdictionBadge jurisdiction="state" />);
    expect(screen.getByText("State Assembly")).toBeInTheDocument();
  });
});

describe("PredictionAvailability", () => {
  it("renders available state with positive indicator", () => {
    render(<PredictionAvailability available={true} jurisdiction="central" />);
    expect(screen.getByText("Market predictions available")).toBeInTheDocument();
  });

  it("renders unavailable state with state firewall reason", () => {
    render(<PredictionAvailability available={false} jurisdiction="state" />);
    expect(screen.getByText(/No market predictions/i)).toBeInTheDocument();
    expect(screen.getByText(/State legislation/i)).toBeInTheDocument();
  });

  it("renders unavailable state with intelligence entity reason", () => {
    render(
      <PredictionAvailability
        available={false}
        jurisdiction="central"
        universeType="intelligence"
      />
    );
    expect(screen.getByText(/Intelligence entity/i)).toBeInTheDocument();
  });
});

describe("MarketRelevanceBadge & CorporateExposureBadge", () => {
  it("renders MarketRelevanceBadge with level", () => {
    render(<MarketRelevanceBadge relevance="HIGH" />);
    expect(screen.getByText("Relevance: HIGH")).toBeInTheDocument();
  });

  it("renders CorporateExposureBadge with count", () => {
    render(<CorporateExposureBadge count={5} />);
    expect(screen.getByText("5 Exposures")).toBeInTheDocument();
  });

  it("renders CorporateExposureBadge with 0 count", () => {
    render(<CorporateExposureBadge count={0} />);
    expect(screen.getByText("0 Exposures")).toBeInTheDocument();
  });

  it("renders CoverageStatus widget with statutory guarantee", () => {
    render(<CoverageStatus centralBills={20} stateBills={44} companies={70} />);
    expect(screen.getByText("Platform Coverage")).toBeInTheDocument();
    expect(screen.getByText("20 modelled")).toBeInTheDocument();
    expect(screen.getByText("44 intelligence")).toBeInTheDocument();
    expect(screen.getByText(/Statutory 0/i)).toBeInTheDocument();
  });
});
