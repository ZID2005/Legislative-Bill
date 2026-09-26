/**
 * __tests__/components/IntelligenceCompanyFirewall.test.tsx
 * ===========================================================
 * Tests for the Intelligence Company Firewall component.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { IntelligenceCompanyFirewall } from "@/components/firewalls/IntelligenceCompanyFirewall";
import type { CompanyDetailResponse } from "@/types/api";

const mockIntelCompany: Partial<CompanyDetailResponse> = {
  company_name: "Swiggy",
  entity_type: "unlisted_startup",
  universe_type: "intelligence",
  is_quant_eligible: false,
  total_exposures: 5,
  mechanisms: ["Regulatory compliance", "Food safety"],
  operating_states: ["Karnataka", "Maharashtra", "Delhi"],
};

describe("IntelligenceCompanyFirewall", () => {
  it("renders without crashing", () => {
    const { container } = render(<IntelligenceCompanyFirewall />);
    expect(container).toBeTruthy();
  });

  it("shows the firewall heading", () => {
    render(<IntelligenceCompanyFirewall company={mockIntelCompany as CompanyDetailResponse} />);
    expect(
      screen.getByText(/market prediction unavailable for this entity/i)
    ).toBeInTheDocument();
  });

  it("shows company name", () => {
    render(<IntelligenceCompanyFirewall company={mockIntelCompany as CompanyDetailResponse} />);
    expect(screen.getByText(/Swiggy/i)).toBeInTheDocument();
  });

  it("shows available intelligence capabilities", () => {
    render(<IntelligenceCompanyFirewall company={mockIntelCompany as CompanyDetailResponse} />);
    expect(screen.getByText(/Company \/ Entity Profile/i)).toBeInTheDocument();
    expect(screen.getByText(/Documented Legislative Exposure/i)).toBeInTheDocument();
    expect(screen.getByText(/Economic Mechanisms/i)).toBeInTheDocument();
    expect(screen.getByText("Evidence & Sources")).toBeInTheDocument();
  });

  it("explicitly lists what is NOT available", () => {
    render(<IntelligenceCompanyFirewall company={mockIntelCompany as CompanyDetailResponse} />);
    expect(screen.getByText(/Stock return prediction/i)).toBeInTheDocument();
    expect(screen.getByText(/Market direction/i)).toBeInTheDocument();
    expect(screen.getByText(/Decision support records/i)).toBeInTheDocument();
    expect(screen.getByText(/Anticipation bias scores/i)).toBeInTheDocument();
  });

  it("does NOT show any buy/sell signal or price prediction", () => {
    render(<IntelligenceCompanyFirewall company={mockIntelCompany as CompanyDetailResponse} />);
    expect(screen.queryByText(/buy signal/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sell signal/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/price target/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/predicted return/i)).not.toBeInTheDocument();
  });

  it("has accessible section role", () => {
    render(<IntelligenceCompanyFirewall />);
    const section = screen.getByRole("region", { name: /prediction availability status/i });
    expect(section).toBeInTheDocument();
  });
});
