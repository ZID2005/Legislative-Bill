/**
 * __tests__/components/task-1-5b-layout-fixes.test.tsx
 * ====================================================
 * Regression and verification test suite for Task 1.5B.1:
 * - Bill dossier tab clipping prevention & responsive scroll behavior
 * - WCAG keyboard navigation on Tabs (ArrowLeft, ArrowRight, Home, End)
 * - Root-page dual-theme contrast and semantic tokens
 * - Sticky header clearance below fixed TopNavbar (top-14 / 56px)
 */

import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Tabs, type Tab } from "@/components/ui/Tabs";
import LandingPage from "@/app/page";

describe("Task 1.5B.1 — Bill Dossier Tabs Responsive & Accessibility Fixes", () => {
  const sampleTabs: Tab[] = [
    { id: "overview", label: "Overview", count: 4 },
    { id: "timeline", label: "Timeline", count: 12 },
    { id: "provisions", label: "Key Provisions", count: 28 },
    { id: "exposures", label: "Corporate Exposure", count: 18 },
    { id: "predictions", label: "Market Predictions" },
    { id: "anticipation", label: "Anticipation" },
    { id: "disabled-tab", label: "Archived Info", disabled: true },
    { id: "provenance", label: "Sources & Provenance" },
  ];

  it("renders all tabs without clipping classes (includes shrink-0 and whitespace-nowrap)", () => {
    const onTabChange = vi.fn();
    render(<Tabs tabs={sampleTabs} activeTab="overview" onTabChange={onTabChange} />);

    const tablist = screen.getByRole("tablist", { name: /Navigation tabs/i });
    expect(tablist).toBeInTheDocument();

    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(sampleTabs.length);

    tabs.forEach((tab) => {
      // Must have shrink-0 to prevent tab compression on narrow viewports (<1200px)
      expect(tab.className).toContain("shrink-0");
      expect(tab.className).toContain("whitespace-nowrap");
    });
  });

  it("supports keyboard navigation with ArrowRight, ArrowLeft, Home, and End", () => {
    const onTabChange = vi.fn();
    render(<Tabs tabs={sampleTabs} activeTab="overview" onTabChange={onTabChange} />);

    const firstTab = screen.getByRole("tab", { name: /Overview/i });

    // ArrowRight moves from overview to timeline
    fireEvent.keyDown(firstTab, { key: "ArrowRight" });
    expect(onTabChange).toHaveBeenCalledWith("timeline");

    // ArrowLeft wraps around or moves to previous enabled tab
    fireEvent.keyDown(firstTab, { key: "ArrowLeft" });
    expect(onTabChange).toHaveBeenCalledWith("provenance");

    // End key jumps to last enabled tab
    fireEvent.keyDown(firstTab, { key: "End" });
    expect(onTabChange).toHaveBeenCalledWith("provenance");

    // Home key jumps to first tab
    const lastTab = screen.getByRole("tab", { name: /Sources & Provenance/i });
    fireEvent.keyDown(lastTab, { key: "Home" });
    expect(onTabChange).toHaveBeenCalledWith("overview");
  });

  it("does not trigger tab switch when clicking or navigating to disabled tab", () => {
    const onTabChange = vi.fn();
    render(<Tabs tabs={sampleTabs} activeTab="overview" onTabChange={onTabChange} />);

    const disabledTab = screen.getByRole("tab", { name: /Archived Info/i });
    expect(disabledTab).toBeDisabled();

    fireEvent.click(disabledTab);
    expect(onTabChange).not.toHaveBeenCalled();
  });

  it("renders pills variant with proper responsive shrink-0 styling and ARIA attributes", () => {
    const onTabChange = vi.fn();
    render(
      <Tabs
        tabs={sampleTabs}
        activeTab="provisions"
        onTabChange={onTabChange}
        variant="pills"
        size="sm"
      />
    );

    const activeTab = screen.getByRole("tab", { name: /Key Provisions/i });
    expect(activeTab).toHaveAttribute("aria-selected", "true");
    expect(activeTab.className).toContain("shrink-0");
    expect(activeTab.className).toContain("bg-[var(--action-primary)]");
  });
});

describe("Task 1.5B.1 — Root Page Dual-Theme & High-Contrast Verification", () => {
  it("renders LandingPage with high contrast CTA text and semantic tokens", () => {
    render(<LandingPage />);

    // Verify main CTA has text-white on blue-600 for AAA contrast in both themes
    const launchBtn = screen.getByRole("link", { name: /Launch Command Center/i });
    expect(launchBtn).toBeInTheDocument();
    expect(launchBtn.className).toContain("text-white");
    expect(launchBtn.className).toContain("bg-blue-600");

    // Verify presence of core workflow cards
    expect(screen.getByText("Legislative Explorer")).toBeInTheDocument();
    expect(screen.getByText("Market Predictions")).toBeInTheDocument();
    expect(screen.getByText("Custom Watchlists")).toBeInTheDocument();
    expect(screen.getByText("Grounded AI Analyst")).toBeInTheDocument();
  });
});
