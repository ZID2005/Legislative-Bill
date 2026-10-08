/**
 * __tests__/pages/ai-analyst.test.tsx
 * ===================================
 * Test suite for the Grounded AI Analyst Terminal.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import AIAnalystPage from "@/app/ai-analyst/page";
import { aiApi } from "@/lib/api/ai";

// Mock Next.js Link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock aiApi
vi.mock("@/lib/api/ai", () => ({
  aiApi: {
    ask: vi.fn(),
  },
}));

describe("AI Analyst Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders terminal header, welcome message, and refusal guardrails", () => {
    render(<AIAnalystPage />);

    expect(screen.getByText("Institutional AI Analyst Terminal")).toBeInTheDocument();
    expect(screen.getByText(/Grounded Groq LLM/i)).toBeInTheDocument();
    expect(screen.getByText(/Welcome to the Grounded AI Analyst Terminal/i)).toBeInTheDocument();
    expect(screen.getByText(/Institutional Refusal Guardrails Active/i)).toBeInTheDocument();
  });

  it("switches persona to Policy Lead and Investor", () => {
    render(<AIAnalystPage />);

    const policyBtn = screen.getByRole("button", { name: "Policy Lead" });
    fireEvent.click(policyBtn);
    expect(policyBtn).toHaveClass("bg-indigo-600");

    const investorBtn = screen.getByRole("button", { name: "Investor" });
    fireEvent.click(investorBtn);
    expect(investorBtn).toHaveClass("bg-indigo-600");
  });

  it("submits question and renders grounded response with provenance citations", async () => {
    (aiApi.ask as any).mockResolvedValue({
      answer: "The Energy Conservation (Amendment) Act establishes mandatory carbon credit trading schemes.",
      provenance_sources: ["Gazette Notification No. 42", "Ministry of Power Rules"],
      disclaimer: "Analytical explanation only; not investment advice.",
      success: true,
    });

    render(<AIAnalystPage />);

    const input = screen.getByPlaceholderText(/Ask a question grounded in parliamentary records/i);
    fireEvent.change(input, { target: { value: "Explain carbon credit trading provisions." } });

    const submitBtn = screen.getByRole("button", { name: /Ask/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(aiApi.ask).toHaveBeenCalledWith(
        expect.objectContaining({
          question: "Explain carbon credit trading provisions.",
          persona: "INVESTOR",
        })
      );
      expect(screen.getByText(/The Energy Conservation \(Amendment\) Act establishes mandatory carbon credit trading schemes/i)).toBeInTheDocument();
      expect(screen.getByText("Gazette Notification No. 42")).toBeInTheDocument();
    });
  });
});
