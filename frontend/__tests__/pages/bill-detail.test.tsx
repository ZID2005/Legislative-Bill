/**
 * __tests__/pages/bill-detail.test.tsx
 * =====================================
 * Comprehensive unit and integration test suite for the Bill Detail Dossier.
 *
 * Validates all 16 core requirements:
 * 1. Central modelled bill renders prediction section
 * 2. Central non-modelled bill renders prediction-unavailable state
 * 3. State bill renders StatePredictionFirewall
 * 4. State bill does not render prediction metrics
 * 5. Company exposure renders correctly
 * 6. No-exposure state renders properly
 * 7. Procedural timeline with missing dates ("Date not available")
 * 8. Related bills render and link
 * 9. Source & provenance panel renders
 * 10. Watchlist action & modal
 * 11. AI explanation success state
 * 12. AI explanation unavailable fallback state
 * 13. API failure error state with retry
 * 14. Bill not found 404 state
 * 15. Loading skeleton state
 * 16. FACT / DERIVED / INTERPRETATION / PREDICTION semantic badge distinction
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock API clients
vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    getBill: vi.fn(),
    getBillPredictions: vi.fn(),
    getBillCompanies: vi.fn(),
    getBillAnticipation: vi.fn(),
  },
}));

vi.mock("@/lib/api/predictions", () => ({
  predictionsApi: {
    getPredictionDecision: vi.fn(),
    getStakeholderReportByKey: vi.fn(),
  },
}));

vi.mock("@/lib/api/watchlists", () => ({
  watchlistsApi: {
    listWatchlists: vi.fn(),
    createWatchlist: vi.fn(),
    addItem: vi.fn(),
  },
}));

vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    explainBill: vi.fn(),
    ask: vi.fn(),
  },
}));

import BillDetailContent from "@/app/bills/[billId]/BillDetailContent";
import { billsApi } from "@/lib/api/bills";
import { predictionsApi } from "@/lib/api/predictions";
import { watchlistsApi } from "@/lib/api/watchlists";
import { aiApi } from "@/lib/api/ai";
import { ApiError } from "@/lib/errors";
import type { BillDetailResponse, BillPredictionStatusResponse, BillCompanyExposure } from "@/types/api";

// ---------------------------------------------------------------------------
// Test Fixtures
// ---------------------------------------------------------------------------

const mockCentralModelledDetail: BillDetailResponse = {
  bill: {
    bill_id: "the-banking-laws-amendment-bill-2024",
    jurisdiction: "central",
    state: null,
    title: "The Banking Laws (Amendment) Bill, 2024",
    short_title: "Banking Laws Amendment Bill",
    bill_number: "Bill No. 125 of 2024",
    legislature: "Parliament of India",
    house: "Lok Sabha",
    year: 2024,
    introduction_date: "2024-08-09",
    assent_date: null,
    status: "passed_both",
    policy_domain: "Financial Regulation",
    economic_sectors: ["Banking & Financial Services", "Capital Markets"],
    secondary_sectors: ["Insurance"],
    stakeholders: ["Banks", "Depositors", "NBFCs"],
    summary: "A bill to amend statutory frameworks governing commercial banking reserves and depositor protection.",
    company_exposure_count: 5,
    listed_company_exposure_count: 5,
    market_relevance: "HIGH",
    modeling_eligibility: "ELIGIBLE",
    data_sufficiency: "COMPLETE",
    source_url: "https://prsindia.org/billtrack/the-banking-laws-amendment-bill-2024",
    pdf_url: "https://prsindia.org/files/bills_spec/the-banking-laws-amendment-bill-2024.pdf",
    data_quality: "VERIFIED",
  },
  provisions: [
    "Regulatory oversight: Reserve Bank of India",
    "Statutory interaction: Banking Regulation Act, 1949",
  ],
  knowledge: {
    amended_acts: ["Banking Regulation Act, 1949", "State Bank of India Act, 1955"],
    regulatory_authority: "Reserve Bank of India",
    financial_terms: "Modifies capital adequacy ratios and deposit claim thresholds.",
    penalties_or_enforcement: "Regulatory penalties for non-reporting under Section 46.",
    objective: "To strengthen governance in the banking sector and enhance customer convenience.",
    key_provisions: [
      "Regulatory oversight: Reserve Bank of India",
      "Statutory interaction: Banking Regulation Act, 1949",
    ],
  },
  provenance: {
    title: "AUTHORITATIVE",
    introduction_date: "AUTHORITATIVE",
    policy_domain: "DERIVED",
    company_exposure: "DERIVED",
  },
  prediction_available: true,
  related_bills: [
    {
      bill_id: "the-bills-of-lading-bill-2024",
      jurisdiction: "central",
      title: "The Bills of Lading Bill, 2024",
      short_title: "Bills of Lading Bill",
      legislature: "Parliament of India",
      house: "Lok Sabha",
      status: "passed_both",
      economic_sectors: ["Transport / Maritime"],
      secondary_sectors: [],
      stakeholders: [],
      summary: "Regulates maritime transport documentation.",
      company_exposure_count: 3,
      listed_company_exposure_count: 3,
      market_relevance: "HIGH",
      modeling_eligibility: "ELIGIBLE",
      data_sufficiency: "COMPLETE",
      data_quality: "VERIFIED",
    },
  ],
};

const mockCentralPredictions: BillPredictionStatusResponse = {
  available: true,
  has_predictions: true,
  bill_id: "the-banking-laws-amendment-bill-2024",
  jurisdiction: "central",
  total: 1,
  predictions: [
    {
      prediction_id: "pred-sbi-1",
      bill_id: "the-banking-laws-amendment-bill-2024",
      company_isin: "INE062A01020",
      company_name: "State Bank of India",
      company_symbol: "SBIN",
      event_window: "[-1,+1]",
      predicted_direction: "POSITIVE",
      predicted_market_moving: true,
      market_moving_probability: 0.72,
      predicted_impact_strength: "HIGH",
      predicted_confidence: "HIGH",
      model_confidence: 0.88,
      model_version: "v1.0.0",
    },
  ],
  items: [],
};

const mockExposures: BillCompanyExposure[] = [
  {
    bill_id: "the-banking-laws-amendment-bill-2024",
    bill_title: "The Banking Laws (Amendment) Bill, 2024",
    company_id: "sbin",
    company_name: "State Bank of India",
    bill_number: "Bill No. 125 of 2024",
    jurisdiction: "central",
    state: null,
    bill_status: "passed_both",
    sector: "Banking & Financial Services",
    sub_sector: "Public Sector Banks",
    business_activity: "Retail & Corporate Banking",
    exposure_type: "Operational",
    exposure_direction: "POSITIVE",
    exposure_strength: "HIGH",
    direct_indirect: "DIRECT",
    geographic_scope: "National",
    mechanism: "Direct statutory reserve and reporting modification under Banking Regulation Act",
    market_relevance: "HIGH",
    confidence: "HIGH",
    has_evidence: true,
    evidence: [
      {
        claim: "State Bank of India is governed by the statutory reserve modifications.",
        reference: "Section 4 Banking Regulation Act",
        statutory_section: "4",
      },
    ],
    source_urls: ["https://sbi.co.in"],
  },
];

const mockAnticipation = {
  available: true,
  bill_id: "the-banking-laws-amendment-bill-2024",
  bill_record: {
    bill_id: "the-banking-laws-amendment-bill-2024",
    overall_anticipation_score: 0.738,
    overall_classification: "MODERATE_EVIDENCE",
    overall_anticipation_flag: true,
    overall_confidence: "HIGH",
    total_companies_analyzed: 47,
  },
  scores: [
    {
      company_isin: "INE062A01020",
      company_symbol: "SBIN",
      anticipation_score: 0.738,
      classification: "MODERATE_EVIDENCE",
      anticipation_flag: true,
      decision_reason: "Pre-event volume accumulation detected.",
    },
  ],
};

const mockStateBillDetail: BillDetailResponse = {
  bill: {
    bill_id: "karnataka-vs-bill-33-2024",
    jurisdiction: "state",
    state: "Karnataka",
    title: "The Karnataka Cinema (Regulation) (Amendment) Bill, 2024",
    short_title: "Karnataka Cinema Regulation Bill",
    bill_number: "Bill No. 33 of 2024",
    legislature: "Karnataka Legislative Assembly",
    house: "Vidhan Sabha",
    year: 2024,
    introduction_date: "2024-07-22",
    assent_date: null,
    status: "passed_both",
    policy_domain: "Media & Entertainment",
    economic_sectors: ["Media & Entertainment"],
    secondary_sectors: [],
    stakeholders: ["Cinema Exhibitors", "Film Producers", "Audiences"],
    summary: "Amends cinema licensing fee structures across urban local bodies in Karnataka.",
    company_exposure_count: 2,
    listed_company_exposure_count: 1,
    market_relevance: "MEDIUM",
    modeling_eligibility: "NOT_ELIGIBLE",
    data_sufficiency: "COMPLETE",
    source_url: "https://kla.kar.nic.in/assembly/bills/bill33.htm",
    pdf_url: "https://kla.kar.nic.in/assembly/bills/bill33.pdf",
    data_quality: "VERIFIED",
  },
  provisions: [
    "Amends Section 12 to revise municipal theatre license renewal periods.",
  ],
  knowledge: {
    amended_acts: ["Karnataka Cinemas (Regulation) Act, 1964"],
    regulatory_authority: "Karnataka Home & Revenue Department",
    financial_terms: "Revision of local theatre permit renewal duties.",
    penalties_or_enforcement: "Suspension of exhibition license for non-compliance.",
    objective: "To rationalize cinema licensing and support single-screen modernization.",
    key_provisions: [
      "Amends Section 12 to revise municipal theatre license renewal periods.",
    ],
  },
  provenance: {
    title: "AUTHORITATIVE",
    state: "AUTHORITATIVE",
    policy_domain: "DERIVED",
  },
  prediction_available: false,
  related_bills: [],
};

const mockStatePredictions: BillPredictionStatusResponse = {
  available: false,
  has_predictions: false,
  bill_id: "karnataka-vs-bill-33-2024",
  jurisdiction: "state",
  firewall_status: "STATE_QUALITATIVE_ONLY",
  reason: "State legislation does not generate quantitative market predictions under project invariants.",
  message: "State bills are isolated from Central stock market models. Quantitative predictions remain strictly 0.",
  total: 0,
  predictions: [],
  items: [],
};

const mockCentralNonModelledDetail: BillDetailResponse = {
  ...mockCentralModelledDetail,
  bill: {
    ...mockCentralModelledDetail.bill,
    bill_id: "key-issues-and-analysis",
    title: "Key Issues and Analysis in Parliament 2024",
    modeling_eligibility: "NOT_ELIGIBLE",
    market_relevance: "NONE",
  },
  prediction_available: false,
};

const mockCentralNonModelledPredictions: BillPredictionStatusResponse = {
  available: false,
  has_predictions: false,
  bill_id: "key-issues-and-analysis",
  jurisdiction: "central",
  firewall_status: "CENTRAL_NON_MODELLED_BILL",
  reason: "CENTRAL_NON_MODELLED_BILL",
  message: "Bill is not part of the frozen 20 quantitative production set.",
  total: 0,
  predictions: [],
  items: [],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("BillDetailContent — Production Dossier", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(billsApi.getBillPredictions).mockResolvedValue({ available: false, has_predictions: false, total: 0, predictions: [], items: [] } as any);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValue([]);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValue({ available: false } as any);
  });

  // TEST 1: Central modelled bill renders prediction section
  it("1. Central modelled bill renders prediction section", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    // Wait for title
    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    // Switch to predictions tab
    const predTab = screen.getByRole("tab", { name: /Market Predictions/i });
    fireEvent.click(predTab);

    // Verify predictions table renders company and direction
    await waitFor(() => {
      expect(screen.getByText("Central Market Predictions & Impact Modeling")).toBeInTheDocument();
      expect(screen.getByText("State Bank of India")).toBeInTheDocument();
      expect(screen.getByText(/POSITIVE/i)).toBeInTheDocument();
      expect(screen.getByText("1 Model Projections")).toBeInTheDocument();
    });
  });

  // TEST 2: Central non-modelled bill renders prediction-unavailable state
  it("2. Central non-modelled bill renders prediction-unavailable state", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralNonModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralNonModelledPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce([]);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce({ available: false });

    render(<BillDetailContent billId="key-issues-and-analysis" />);

    await waitFor(() => {
      expect(screen.getByText("Key Issues and Analysis in Parliament 2024")).toBeInTheDocument();
    });

    const predTab = screen.getByRole("tab", { name: /Market Predictions/i });
    fireEvent.click(predTab);

    await waitFor(() => {
      expect(screen.getByText("Market Impact Predictions")).toBeInTheDocument();
      expect(screen.getByText(/Bill is not part of the frozen 20 quantitative production set/i)).toBeInTheDocument();
    });
  });

  // TEST 3 & 4: State bill renders StatePredictionFirewall and does NOT render prediction metrics
  it("3 & 4. State bill renders StatePredictionFirewall with 0 prediction metrics", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockStateBillDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockStatePredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce([]);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce({ available: false, reason: "STATE_ANTICIPATION_NOT_APPLICABLE" });

    render(<BillDetailContent billId="karnataka-vs-bill-33-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Karnataka Cinema (Regulation) (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const predTab = screen.getByRole("tab", { name: /Market Predictions/i });
    fireEvent.click(predTab);

    await waitFor(() => {
      // Must render firewall title
      expect(
        screen.getByText("Market prediction is not currently available for State legislation")
      ).toBeInTheDocument();
      expect(screen.getByText(/Karnataka Assembly — Level 2 Legislative Intelligence/i)).toBeInTheDocument();
      // Must NOT render prediction metric headers or quantitative models
      expect(screen.queryByText(/Projected Direction/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Market Moving Probability/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Model Projections/i)).not.toBeInTheDocument();
      // Barred capability is explicitly acknowledged in firewall list
      expect(screen.getByText(/Buy \/ Sell \/ Hold signal/i)).toBeInTheDocument();
    });
  });

  // TEST 5: Company exposure renders correctly
  it("5. Company exposure renders correctly with search and filtering", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const expTab = screen.getByRole("tab", { name: /Corporate Exposure/i });
    fireEvent.click(expTab);

    await waitFor(() => {
      expect(screen.getByText("Documented Corporate Exposures")).toBeInTheDocument();
      expect(screen.getByText("State Bank of India")).toBeInTheDocument();
      expect(screen.getByText(/Retail & Corporate Banking/i)).toBeInTheDocument();
      expect(screen.getAllByText("DIRECT").length).toBeGreaterThanOrEqual(1);
    });
  });

  // TEST 6: No-exposure state
  it("6. No-exposure state renders informative message", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockStateBillDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockStatePredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce([]);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce({ available: false });

    render(<BillDetailContent billId="karnataka-vs-bill-33-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Karnataka Cinema (Regulation) (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const expTab = screen.getByRole("tab", { name: /Corporate Exposure/i });
    fireEvent.click(expTab);

    await waitFor(() => {
      expect(screen.getByText("No Documented Corporate Exposures")).toBeInTheDocument();
    });
  });

  // TEST 7: Procedural timeline with missing dates
  it("7. Procedural timeline renders with missing dates as 'Date not available'", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("Procedural Journey")).toBeInTheDocument();
      expect(screen.getAllByText("Date not available").length).toBeGreaterThanOrEqual(1);
    });
  });

  // TEST 8: Related bills
  it("8. Related bills list renders and links to related bill", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("Related Legislation")).toBeInTheDocument();
      expect(screen.getByText("Bills of Lading Bill")).toBeInTheDocument();
    });
  });

  // TEST 9: Source & provenance panel
  it("9. Source and provenance panel renders official document links and field audit", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const provTab = screen.getByRole("tab", { name: /Sources & Provenance/i });
    fireEvent.click(provTab);

    await waitFor(() => {
      expect(screen.getByText("Authoritative Source & Data Provenance")).toBeInTheDocument();
      expect(screen.getByText("Field-Level Provenance Audit Map")).toBeInTheDocument();
    });
  });

  // TEST 10: Watchlist action opens modal
  it("10. Watchlist action button opens watchlist modal", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);
    vi.mocked(watchlistsApi.listWatchlists).mockResolvedValueOnce([
      {
        watchlist_id: "wl-1",
        user_id: "user-1",
        tenant_id: "tenant-1",
        name: "Financial Services Tracker",
        description: null,
        is_default: true,
        is_active: true,
        created_at: "2026-09-19T00:00:00Z",
        updated_at: "2026-09-19T00:00:00Z",
        items_count: 2,
        items: [],
        rules: [],
      },
    ]);

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const watchlistBtn = screen.getByRole("button", { name: /Add bill to watchlist/i });
    fireEvent.click(watchlistBtn);

    await waitFor(() => {
      expect(screen.getByText("Select Target Watchlist:")).toBeInTheDocument();
      expect(screen.getByText("Financial Services Tracker")).toBeInTheDocument();
    });
  });

  // TEST 11: AI explanation success
  it("11. AI explanation success displays grounded content and sources", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);
    vi.mocked(aiApi.explainBill).mockResolvedValueOnce({
      content: "This bill modifies reserve ratios for scheduled commercial banks.",
      context_type: "bill",
      context_id: "the-banking-laws-amendment-bill-2024",
      persona: "GENERAL_PUBLIC",
      operation: "WHY_IT_MATTERS",
      success: true,
      is_cached: false,
      disclaimer: "Analytical explanation only; not investment advice.",
      provenance_sources: ["PRS Legislative Research", "Parliament Gazettes"],
    });

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const aiTab = screen.getByRole("tab", { name: /AI Copilot/i });
    fireEvent.click(aiTab);

    await waitFor(() => {
      expect(screen.getByText("Grounded AI Legislative Copilot")).toBeInTheDocument();
    });

    const promptBtn = screen.getByText(/What does this bill change\?/i);
    fireEvent.click(promptBtn);

    await waitFor(() => {
      expect(screen.getByText("AI Analytical Synthesis")).toBeInTheDocument();
      expect(screen.getByText(/This bill modifies reserve ratios for scheduled commercial banks/i)).toBeInTheDocument();
      expect(screen.getByText(/PRS Legislative Research, Parliament Gazettes/i)).toBeInTheDocument();
    });
  });

  // TEST 12: AI explanation unavailable fallback
  it("12. AI explanation unavailable displays clean fallback without error crash", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);
    vi.mocked(aiApi.explainBill).mockRejectedValueOnce(new Error("Groq API rate limit exceeded"));

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    const aiTab = screen.getByRole("tab", { name: /AI Copilot/i });
    fireEvent.click(aiTab);

    const promptBtn = screen.getByText(/What does this bill change\?/i);
    fireEvent.click(promptBtn);

    await waitFor(() => {
      expect(screen.getByText(/Fallback Notice:/i)).toBeInTheDocument();
      expect(screen.getByText(/AI Explanation Copilot is operating in offline mode/i)).toBeInTheDocument();
    });
  });

  // TEST 13: API failure with retry
  it("13. API failure displays error state", async () => {
    vi.mocked(billsApi.getBill).mockRejectedValueOnce(
      new ApiError({
        message: "Internal Server Error",
        status: 500,
        code: "SERVER_ERROR",
        userMessage: "Legislative service is temporarily unavailable.",
      })
    );

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("Legislative service is temporarily unavailable.")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Try again/i })).toBeInTheDocument();
    });
  });

  // TEST 14: Bill not found 404 state
  it("14. Bill not found 404 displays institutional not found card", async () => {
    vi.mocked(billsApi.getBill).mockRejectedValueOnce(
      new ApiError({
        message: "Bill not found",
        status: 404,
        code: "NOT_FOUND",
        userMessage: "Bill with ID 'unknown-bill' not found.",
      })
    );

    render(<BillDetailContent billId="unknown-bill" />);

    await waitFor(() => {
      expect(screen.getByText("Legislative Bill Not Found")).toBeInTheDocument();
      expect(screen.getByText(/unknown-bill/i)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: /View All Bills/i })).toBeInTheDocument();
    });
  });

  // TEST 15: Loading state
  it("15. Loading state renders skeleton placeholders", () => {
    vi.mocked(billsApi.getBill).mockReturnValue(new Promise(() => {})); // Never resolves
    vi.mocked(billsApi.getBillPredictions).mockReturnValue(new Promise(() => {}));
    vi.mocked(billsApi.getBillCompanies).mockReturnValue(new Promise(() => {}));
    vi.mocked(billsApi.getBillAnticipation).mockReturnValue(new Promise(() => {}));
    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);
    expect(screen.getByLabelText("Loading bill dossier")).toBeInTheDocument();
  });

  // TEST 16: FACT / DERIVED / INTERPRETATION / PREDICTION distinction
  it("16. Distinguishes FACT, DERIVED, INTERPRETATION, and PREDICTION badges", async () => {
    vi.mocked(billsApi.getBill).mockResolvedValueOnce(mockCentralModelledDetail);
    vi.mocked(billsApi.getBillPredictions).mockResolvedValueOnce(mockCentralPredictions);
    vi.mocked(billsApi.getBillCompanies).mockResolvedValueOnce(mockExposures);
    vi.mocked(billsApi.getBillAnticipation).mockResolvedValueOnce(mockAnticipation);

    render(<BillDetailContent billId="the-banking-laws-amendment-bill-2024" />);

    await waitFor(() => {
      expect(screen.getByText("The Banking Laws (Amendment) Bill, 2024")).toBeInTheDocument();
    });

    // Switch to Stakeholders tab to see all 4 semantic tiers together
    const shTab = screen.getByRole("tab", { name: /Stakeholders/i });
    fireEvent.click(shTab);

    await waitFor(() => {
      expect(screen.getByText("1. Official Statutory Fact")).toBeInTheDocument();
      expect(screen.getByText("2. Deterministic Mapping Vector")).toBeInTheDocument();
      expect(screen.getByText("3. Analytical Impact Interpretation")).toBeInTheDocument();
      expect(screen.getByText("4. Market & Sensitivity Tier")).toBeInTheDocument();
    });
  });
});
