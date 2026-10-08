/**
 * __tests__/pages/states.test.tsx
 * ================================
 * Test suite for Sub-National Legislative Intelligence Registry and State Detail Dossier.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import StatesPage from "@/app/states/page";
import StateDetailPage from "@/app/states/[state]/page";
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
  },
}));

describe("States Page (Registry)", () => {
  it("renders registry title and invariant stats (4 active, 44 acts, 0 predictions)", () => {
    render(<StatesPage />);

    expect(screen.getByText("Sub-National Legislative Intelligence Registry")).toBeInTheDocument();
    expect(screen.getByText("Implemented States")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("44")).toBeInTheDocument();
    expect(screen.getByText("State Stock Predictions")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("24")).toBeInTheDocument();
  });

  it("renders the 4 active production pilot states", () => {
    render(<StatesPage />);

    expect(screen.getByText("Andhra Pradesh")).toBeInTheDocument();
    expect(screen.getByText("Karnataka")).toBeInTheDocument();
    expect(screen.getByText("Kerala")).toBeInTheDocument();
    expect(screen.getByText("Telangana")).toBeInTheDocument();
  });

  it("enforces and displays the State Prediction Firewall notice", () => {
    render(<StatesPage />);

    expect(screen.getByText(/Market prediction is not currently available for State legislation/i)).toBeInTheDocument();
  });
});

describe("State Detail Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (billsApi.listBills as any).mockResolvedValue({
      items: [
        {
          bill_id: "karnataka-vs-bill-33-2024",
          title: "Karnataka Platform Based Gig Workers Bill, 2024",
          bill_number: "LA-33-2024",
          year: 2024,
          status: "ENACTED",
          jurisdiction: "state",
          state: "Karnataka",
          company_exposure_count: 5,
        },
      ],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    });
  });

  it("renders state header, firewall, and assembly acts table", async () => {
    const pageComponent = await StateDetailPage({
      params: Promise.resolve({ state: "Karnataka" }),
    });
    render(pageComponent);

    expect(screen.getByRole("heading", { level: 1, name: "Karnataka" })).toBeInTheDocument();
    expect(screen.getByText(/Karnataka Legislative Assembly/i)).toBeInTheDocument();
    expect(screen.getByText(/Market prediction is not currently available for State legislation/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Karnataka Platform Based Gig Workers Bill, 2024")).toBeInTheDocument();
      expect(screen.getByText("ENACTED")).toBeInTheDocument();
    });
  });
});
