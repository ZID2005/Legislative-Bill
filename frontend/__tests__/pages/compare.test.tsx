/**
 * __tests__/pages/compare.test.tsx
 * =================================
 * Test suite for the Statutory Comparison Workspace.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import BillComparePage from "@/app/bills/compare/page";
import { billsApi } from "@/lib/api/bills";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock billsApi
vi.mock("@/lib/api/bills", () => ({
  billsApi: {
    listBills: vi.fn(),
    getBill: vi.fn(),
    compareBills: vi.fn(),
    getBillCompanies: vi.fn(),
  },
}));

const mockBill1 = {
  bill_id: "bill_001_energy_conservation",
  title: "The Energy Conservation (Amendment) Act, 2022",
  bill_number: "Act No. 19 of 2022",
  year: 2022,
  status: "ENACTED",
  jurisdiction: "central",
  ministry: "Ministry of Power",
  provisions: ["Mandatory carbon credit trading scheme", "Energy consumption standards for large industries"],
  company_exposures: [
    { company_id: "INE002A01018", company_name: "Reliance Industries", directness: "DIRECT" },
    { company_id: "INE081A01012", company_name: "Tata Power", directness: "DIRECT" },
  ],
};

const mockBill2 = {
  bill_id: "bill_002_dpdp",
  title: "The Digital Personal Data Protection Act, 2023",
  bill_number: "Act No. 22 of 2023",
  year: 2023,
  status: "ENACTED",
  jurisdiction: "central",
  ministry: "Ministry of Electronics and Information Technology",
  provisions: ["Establishment of Data Protection Board of India", "Penalties up to ₹250 crore for significant data breaches"],
  company_exposures: [
    { company_id: "INE002A01018", company_name: "Reliance Industries", directness: "INDIRECT" },
    { company_id: "INE009A01021", company_name: "Infosys Limited", directness: "DIRECT" },
  ],
};

describe("Bill Comparison Workspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (billsApi.listBills as any).mockResolvedValue({
      items: [
        { bill_id: mockBill1.bill_id, title: mockBill1.title },
        { bill_id: mockBill2.bill_id, title: mockBill2.title },
      ],
      total: 2,
    });
    (billsApi.getBill as any).mockImplementation((id: string) => {
      if (id === mockBill1.bill_id) return Promise.resolve(mockBill1);
      return Promise.resolve(mockBill2);
    });
    (billsApi.getBillCompanies as any).mockImplementation((id: string) => {
      if (id === mockBill1.bill_id) return Promise.resolve(mockBill1.company_exposures);
      return Promise.resolve(mockBill2.company_exposures);
    });
    (billsApi.compareBills as any).mockResolvedValue({
      bill1: mockBill1,
      bill2: mockBill2,
    });
  });

  it("renders page header and statutory comparison controls", async () => {
    render(<BillComparePage />);

    expect(screen.getByText("Statutory Comparison Workbench")).toBeInTheDocument();
    expect(screen.getByText(/Side-by-side analytical comparison/i)).toBeInTheDocument();
  });

  it("loads and displays both bills metadata diff side-by-side", async () => {
    render(<BillComparePage />);

    await waitFor(() => {
      expect(screen.getAllByText("The Energy Conservation (Amendment) Act, 2022").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("The Digital Personal Data Protection Act, 2023").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("ENACTED").length).toBeGreaterThanOrEqual(2);
      expect(screen.getAllByText("Regulatory").length).toBeGreaterThanOrEqual(2);
    });
  });

  it("identifies corporate exposure overlap (Reliance Industries)", async () => {
    render(<BillComparePage />);

    await waitFor(() => {
      expect(screen.getByText("2. Corporate Exposure Overlap Matrix")).toBeInTheDocument();
      expect(screen.getByText("Reliance Industries")).toBeInTheDocument();
      expect(screen.getByText("DUAL IMPACT")).toBeInTheDocument();
    });
  });
});
