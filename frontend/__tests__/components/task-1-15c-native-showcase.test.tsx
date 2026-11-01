/**
 * __tests__/components/task-1-15c-native-showcase.test.tsx
 * ========================================================
 * Unit test suite for Task 1.15C:
 * Seance Native Animated Intelligence Showcase & Device Mockup Integration.
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  LegislativeJourneyVisual,
  WorkspaceCommandCenterVisual,
  CorporateExposureNetworkVisual,
  StateIntelligenceMapVisual,
  WatchlistIntelligenceVisual,
  AlertIntelligenceVisual,
  SeanceMobileShowcase,
  WorkspaceLaunchVisual,
} from "@/components/onboarding/showcase";
import {
  FeatureCarousel,
  SEANCE_EIGHT_STAGES,
} from "@/components/ui/feature-carousel";
import { IPhone17ProMax } from "@/components/ui/apple-iphone-17-pro";

describe("Task 1.15C — Native Intelligence Showcase Components", () => {
  it("renders Stage 01 LegislativeJourneyVisual with accurate institutional terminology", () => {
    render(<LegislativeJourneyVisual />);
    expect(screen.getByText(/The Telecommunications Act, 2023/i)).toBeDefined();
    expect(screen.getByText(/Bill Introduced/i)).toBeDefined();
    expect(screen.getByText(/Parliamentary Review/i)).toBeDefined();
    expect(screen.getByText(/Bicameral Passage/i)).toBeDefined();
    expect(screen.getAllByText(/Presidential Assent/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/GENERIC LEGISLATIVE LIFECYCLE MODEL/i)).toBeDefined();
  });

  it("renders Stage 02 WorkspaceCommandCenterVisual with counters and demo notice", () => {
    render(<WorkspaceCommandCenterVisual />);
    expect(screen.getByText(/Workspace Telemetry Stream/i)).toBeDefined();
    expect(screen.getByText(/ILLUSTRATIVE DEMO DATA/i)).toBeDefined();
    expect(screen.getByText("20")).toBeDefined();
    expect(screen.getByText("44")).toBeDefined();
    expect(screen.getByText("47")).toBeDefined();
    expect(screen.getByText(/Lok Sabha \/ Digital Sansad/i)).toBeDefined();
  });

  it("renders Stage 03 CorporateExposureNetworkVisual with direct and indirect relationships", () => {
    render(<CorporateExposureNetworkVisual />);
    expect(screen.getByText(/Legislative Corporate Exposure Graph/i)).toBeDefined();
    expect(screen.getAllByText(/DIRECT/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/INDIRECT/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/BHARTIARTL/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/47 QUANT SECURITIES UNIVERSE/i)).toBeDefined();
  });

  it("renders Stage 04 StateIntelligenceMapVisual with StatePredictionFirewall guarantee", () => {
    render(<StateIntelligenceMapVisual />);
    expect(screen.getByText(/India Statutory Jurisdiction Map/i)).toBeDefined();
    expect(screen.getByText(/STATE PREDICTION FIREWALL GUARANTEE/i)).toBeDefined();
    expect(screen.getByText(/0.00% LEAKAGE/i)).toBeDefined();
    expect(screen.getByText(/Sub-national state legislation/i)).toBeDefined();
  });

  it("renders Stage 05 WatchlistIntelligenceVisual with tab switching", () => {
    render(<WatchlistIntelligenceVisual />);
    expect(screen.getByText(/Priority Regulatory Watchlists/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /Statutory Acts/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /Quant Equities/i })).toBeDefined();

    // Click Quant Equities tab
    fireEvent.click(screen.getByRole("button", { name: /Quant Equities/i }));
    expect(screen.getByText("BHARTIARTL")).toBeDefined();
    expect(screen.getByText("HDFCBANK")).toBeDefined();
  });

  it("renders Stage 06 AlertIntelligenceVisual with radial gauge and simulated trigger", () => {
    render(<AlertIntelligenceVisual />);
    expect(screen.getByText(/Alert Thresholds & Multi-Channel Delivery/i)).toBeDefined();
    expect(screen.getAllByText(/85%/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/HIGH SEVERITY/i)).toBeDefined();
    expect(screen.getByText(/SIMULATED TRIGGER EVENT/i)).toBeDefined();
    expect(screen.getByText(/In-App Telemetry/i)).toBeDefined();
  });

  it("renders Stage 07 SeanceMobileShowcase with IPhone17ProMax and native mobile app UI", () => {
    render(<SeanceMobileShowcase />);
    expect(screen.getByLabelText(/Apple iPhone 17 Pro Max Device Frame/i)).toBeDefined();
    expect(screen.getByText(/LIVE DOSSIER/i)).toBeDefined();
    expect(screen.getByText(/The Telecommunications Act, 2023/i)).toBeDefined();
    expect(screen.getByText(/GROUNDED AI ANALYST/i)).toBeDefined();
    expect(screen.getByText(/Act 44 of 2023, §14\(2\)/i)).toBeDefined();
  });

  it("interacts with Dynamic Island on IPhone17ProMax component", () => {
    const handleTap = vi.fn();
    render(
      <IPhone17ProMax
        dynamicIslandSize="default"
        onDynamicIslandTap={handleTap}
      >
        <div>Content</div>
      </IPhone17ProMax>
    );

    const island = screen.getByRole("button", { name: /Dynamic Island/i });
    expect(island).toBeDefined();
    fireEvent.click(island);
    expect(handleTap).toHaveBeenCalled();
  });

  it("renders Stage 08 WorkspaceLaunchVisual with verification checklist", () => {
    render(<WorkspaceLaunchVisual />);
    expect(screen.getByText(/Workspace Deployment Matrix/i)).toBeDefined();
    expect(screen.getByText(/ALL SYSTEMS VERIFIED/i)).toBeDefined();
    expect(screen.getByText(/Statutory Intelligence Engine/i)).toBeDefined();
    expect(screen.getByText(/Sub-National Firewall/i)).toBeDefined();
    expect(screen.getByText(/CLICK LAUNCH COMMAND CENTER →/i)).toBeDefined();
  });

  it("renders all 8 stages inside FeatureCarousel without screenshot image dependencies", () => {
    const { rerender } = render(
      <FeatureCarousel stages={SEANCE_EIGHT_STAGES} activeStep={1} />
    );
    expect(screen.getByText("STAGE 01 · FOUNDATION")).toBeDefined();
    expect(screen.getByText(/The Telecommunications Act, 2023/i)).toBeDefined();

    // Verify Stage 7 mounts mobile showcase
    rerender(<FeatureCarousel stages={SEANCE_EIGHT_STAGES} activeStep={7} />);
    expect(screen.getByText("STAGE 07 · REASONING ENGINE")).toBeDefined();
    expect(screen.getByLabelText(/Apple iPhone 17 Pro Max Device Frame/i)).toBeDefined();

    // Verify Stage 8 mounts launch matrix
    rerender(<FeatureCarousel stages={SEANCE_EIGHT_STAGES} activeStep={8} />);
    expect(screen.getByText("STAGE 08 · COMMAND CENTER")).toBeDefined();
    expect(screen.getByText(/Workspace Deployment Matrix/i)).toBeDefined();
  });
});
