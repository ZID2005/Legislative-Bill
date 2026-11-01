/**
 * __tests__/components/task-1-5b-4-product-polish.test.tsx
 * ==============================================================
 * Comprehensive test suite for Task 1.5B.4:
 * Seance Product Polish & Dashboard Usability Pass
 *
 * Validates:
 * 1. CorporateExposureTable Epistemic Guidance Banner explaining corporate exposure vs quantitative models
 * 2. CorporateExposureTable State Isolation Firewall preventing misleading prediction links for state bills
 * 3. CorporateExposureTable high-contrast active filter styling (text-white font-semibold)
 * 4. CorporateExposureTable expanded drawer with Portfolio cross-reference link ("Cross-reference in Portfolio →")
 * 5. EpistemicBadge component rendering across FACT, OBSERVED, DERIVED, PREDICTION tokens
 * 6. EmptyState component accessible presentation (role="status", title, description, and action)
 */

import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CorporateExposureTable } from "@/components/bills/CorporateExposureTable";
import { EpistemicBadge } from "@/components/ui/EpistemicBadge";
import { EmptyState } from "@/components/ui/Skeleton";
import type { BillCompanyExposure } from "@/types/api";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: any }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

const mockCentralExposure: BillCompanyExposure = {
  bill_id: "the-banking-laws-amendment-bill-2024",
  bill_title: "The Banking Laws (Amendment) Bill, 2024",
  company_id: "comp_sbi_1",
  company_name: "State Bank of India",
  sector: "Financials",
  sub_sector: "Public Sector Banking",
  business_activity: "Commercial banking, lending, statutory reserve deposits",
  exposure_type: "REGULATORY_COMPLIANCE",
  exposure_direction: "NEGATIVE",
  exposure_strength: "HIGH",
  direct_indirect: "DIRECT",
  geographic_scope: "NATIONAL",
  mechanism: "Regulatory capital requirements and priority sector lending targets",
  market_relevance: "Direct statutory impact from regulatory liquidity norms.",
  confidence: "HIGH",
  jurisdiction: "central",
  bill_status: "PASSED",
  has_evidence: true,
  evidence: [],
  source_urls: ["https://prsindia.org/billtrack/banking-laws"],
};

const mockStateExposure: BillCompanyExposure = {
  bill_id: "karnataka-electricity-reform-bill-2024",
  bill_title: "Karnataka Electricity Reform Bill, 2024",
  company_id: "comp_kptl_1",
  company_name: "Karnataka Power Transmission Ltd",
  sector: "Utilities",
  sub_sector: "Power Transmission",
  business_activity: "State electric grid transmission and distribution",
  exposure_type: "OPERATIONAL_MANDATE",
  exposure_direction: "NEUTRAL",
  exposure_strength: "HIGH",
  direct_indirect: "DIRECT",
  geographic_scope: "STATE",
  mechanism: "State transmission tariff guidelines and renewable energy purchase obligations",
  market_relevance: "State electricity regulatory commission statutory mandate.",
  confidence: "HIGH",
  jurisdiction: "state",
  state: "Karnataka",
  bill_status: "PENDING",
  has_evidence: true,
  evidence: [],
  source_urls: [],
};

describe("Task 1.5B.4 — CorporateExposureTable Usability & Epistemic Clarifications", () => {
  it("renders the Epistemic Distinction banner explaining corporate exposure vs quantitative models", () => {
    render(
      <CorporateExposureTable
        exposures={[mockCentralExposure]}
      />
    );

    expect(screen.getByText(/Epistemic Distinction:/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Corporate exposures document verified statutory touchpoints/i)
    ).toBeInTheDocument();
  });

  it("applies high-contrast text-white on active filter button", () => {
    render(
      <CorporateExposureTable
        exposures={[mockCentralExposure]}
      />
    );

    const allButton = screen.getByRole("button", { name: "All Types" });
    expect(allButton.className).toContain("text-white");
    expect(allButton.className).toContain("font-semibold");
  });

  it("links Central bill exposures to Predictions engine with encoded company search query", () => {
    render(
      <CorporateExposureTable
        exposures={[mockCentralExposure]}
      />
    );

    const predLink = screen.getByRole("link", { name: /Predictions ↗/i });
    expect(predLink).toHaveAttribute(
      "href",
      "/predictions?search=State%20Bank%20of%20India"
    );
  });

  it("strictly enforces State Isolation firewall by hiding prediction links for State bills", () => {
    render(
      <CorporateExposureTable
        exposures={[mockStateExposure]}
      />
    );

    // Should NOT have a Predictions link
    expect(screen.queryByRole("link", { name: /Predictions ↗/i })).not.toBeInTheDocument();

    // Should display State Isolation badge
    expect(
      screen.getByText(/State Isolation \(0 Predictions\)/i)
    ).toBeInTheDocument();
  });

  it("renders portfolio cross-reference link in expanded details drawer", () => {
    render(
      <CorporateExposureTable
        exposures={[mockCentralExposure]}
      />
    );

    // Click "Details" button to expand drawer
    const detailsBtn = screen.getByRole("button", { name: /Toggle evidence for State Bank of India/i });
    fireEvent.click(detailsBtn);

    const portfolioLink = screen.getByRole("link", { name: /Check Portfolio Exposure →/i });
    expect(portfolioLink).toHaveAttribute("href", "/portfolio");
    expect(portfolioLink).toHaveAttribute(
      "title",
      "Evaluate exposure of this measure across your tracked holdings in Portfolio Exposure"
    );
  });
});

describe("Task 1.5B.4 — EpistemicBadge Institutional Classifications", () => {
  it("renders FACT token with bracket and authoritative description", () => {
    render(<EpistemicBadge type="FACT" showBracket />);
    expect(screen.getByText("[FACT]")).toBeInTheDocument();
  });

  it("renders OBSERVED token with bracket", () => {
    render(<EpistemicBadge type="OBSERVED" showBracket />);
    expect(screen.getByText("[OBSERVED]")).toBeInTheDocument();
  });

  it("renders DERIVED token with bracket", () => {
    render(<EpistemicBadge type="DERIVED" showBracket />);
    expect(screen.getByText("[DERIVED]")).toBeInTheDocument();
  });

  it("renders PREDICTION token with bracket", () => {
    render(<EpistemicBadge type="PREDICTION" showBracket />);
    expect(screen.getByText("[PREDICTION]")).toBeInTheDocument();
  });
});

describe("Task 1.5B.4 — EmptyState Standardized Presentation", () => {
  it("renders accessible status role with title, description, and action button", () => {
    render(
      <EmptyState
        title="No Monitored Holdings"
        description="Your portfolio currently contains zero tracked assets."
        action={<button className="btn-test">Add Holding</button>}
      />
    );

    const container = screen.getByRole("status");
    expect(container).toBeInTheDocument();
    expect(screen.getByText("No Monitored Holdings")).toBeInTheDocument();
    expect(screen.getByText("Your portfolio currently contains zero tracked assets.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add Holding" })).toBeInTheDocument();
  });
});
