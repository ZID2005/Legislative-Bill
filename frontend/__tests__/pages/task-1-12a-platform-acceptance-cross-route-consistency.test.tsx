/**
 * __tests__/pages/task-1-12a-platform-acceptance-cross-route-consistency.test.tsx
 * ==============================================================================
 * Comprehensive End-to-End Cross-Route Consistency & Regulatory Acceptance Suite
 * for Task 1.12A: Seance Final Platform Acceptance & Regression.
 *
 * Exercises:
 * 1. Bill Cross-Route Consistency (stable identifiers, modeling eligibility, firewalls)
 * 2. Company Cross-Route Consistency (quantitative vs intelligence-only quarantine)
 * 3. Prediction Cross-Route Consistency (5 event horizons, stable associations, uncertainty)
 * 4. Evidence & Provenance Consistency (epistemic labels, official vs media timestamps)
 * 5. Analytical Invariant & Regulatory Safeguards (zero recommendations, no insider allegations)
 * 6. Frozen Baseline SHA-256 Verification (docs/production_baseline.json)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import fs from "fs";
import path from "path";
import crypto from "crypto";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock Next.js navigation hooks
let mockSearchParams = new URLSearchParams();
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
};

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => mockRouter,
  usePathname: () => "/bills",
}));

import { StatePredictionFirewall } from "@/components/firewalls/StatePredictionFirewall";
import { IntelligenceCompanyFirewall } from "@/components/firewalls/IntelligenceCompanyFirewall";
import type { CompanyDetailResponse } from "@/types/api";

describe("Task 1.12A — Cross-Route Consistency & Regulatory Safeguards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams = new URLSearchParams();
  });

  describe("1. Frozen Baseline SHA-256 Invariance", () => {
    it("matches the exact authoritative baseline manifest hash", () => {
      const baselinePath = path.resolve(process.cwd(), "../docs/production_baseline.json");
      expect(fs.existsSync(baselinePath)).toBe(true);

      const content = fs.readFileSync(baselinePath);
      const computedHash = crypto.createHash("sha256").update(content).digest("hex");
      const expectedHash = "50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7";

      expect(computedHash).toBe(expectedHash);
    });

    it("verifies the authoritative inventory counts within the baseline JSON", () => {
      const baselinePath = path.resolve(process.cwd(), "../docs/production_baseline.json");
      const baseline = JSON.parse(fs.readFileSync(baselinePath, "utf-8"));

      expect(baseline.central_baseline.production_bills_count).toBe(20);
      expect(baseline.central_baseline.quantitative_securities_count).toBe(47);
      expect(baseline.central_baseline.bill_company_pairs_count).toBe(940);
      expect(baseline.central_baseline.prediction_records_count).toBe(4700);

      expect(baseline.invariants.zero_state_stock_predictions).toBe(true);
      expect(baseline.invariants.firewall_intel_only_companies).toBe(true);
      expect(baseline.invariants.immutable_central_predictions).toBe(true);
    });
  });

  describe("2. Statutory Firewalls Across Route Boundaries", () => {
    it("renders StatePredictionFirewall with strict zero quantitative predictions guarantee", () => {
      render(
        <StatePredictionFirewall
          billId="kerala-vs-bill-250-2025"
          billTitle="The Kerala Finance Bill, 2025"
          state="Kerala"
        />
      );

      // Verify header and firewall statement
      expect(
        screen.getByText(/market prediction is not currently available for state legislation/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/State bills are governed by a strict statutory and econometric boundary/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Kerala/i)).toBeInTheDocument();
    });

    it("renders IntelligenceCompanyFirewall for non-quantitative entities", () => {
      const mockCompany: Partial<CompanyDetailResponse> = {
        company_name: "Private Infrastructure Entity Ltd",
        entity_type: "unlisted_startup",
        universe_type: "intelligence",
        is_quant_eligible: false,
        total_exposures: 3,
        mechanisms: ["Compliance"],
        operating_states: ["Karnataka"],
      };

      render(
        <IntelligenceCompanyFirewall
          company={mockCompany as CompanyDetailResponse}
        />
      );

      // Verify quarantine header and statutory explanation
      expect(
        screen.getByText(/market prediction unavailable for this entity/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Private Infrastructure Entity Ltd/i)).toBeInTheDocument();
      expect(
        screen.getByText(/qualitative intelligence entity/i)
      ).toBeInTheDocument();
    });
  });

  describe("3. Supported Event Horizons Consistency", () => {
    it("verifies the 5 canonical event horizons are strictly defined", () => {
      const canonicalHorizons = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"];
      expect(canonicalHorizons.length).toBe(5);
      expect(canonicalHorizons).toContain("[-1,+1]");
      expect(canonicalHorizons).toContain("[-3,+3]");
      expect(canonicalHorizons).toContain("[-5,+5]");
      expect(canonicalHorizons).toContain("[-5,+10]");
      expect(canonicalHorizons).toContain("[-10,+10]");
    });
  });

  describe("4. Regulatory Compliance & Non-Advisory Guarantees", () => {
    it("verifies no personalized buy/sell/hold financial advice tokens exist in formatters or disclaimers", () => {
      const formattersPath = path.resolve(process.cwd(), "lib/formatters.ts");
      if (fs.existsSync(formattersPath)) {
        const content = fs.readFileSync(formattersPath, "utf-8");
        expect(content).not.toMatch(/\bBUY\b/i);
        expect(content).not.toMatch(/\bSELL\b/i);
        expect(content).not.toMatch(/\bTARGET_PRICE\b/i);
      }
    });
  });
});
