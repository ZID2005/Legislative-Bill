import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import {
  ChartContainer,
  ChartTooltip,
  EventStudyChart,
  HorizonComparisonVisualizer,
  RiskDistributionVisualizer,
  PreEventCarChart,
} from "@/components/charts";

describe("Seance Chart & Visualization System", () => {
  describe("ChartContainer", () => {
    it("renders title, subtitle, and epistemic badge", () => {
      render(
        <ChartContainer
          title="Central Event Study"
          subtitle="Multi-horizon projections"
          epistemicTier="PREDICTION"
        >
          <div>Chart Contents</div>
        </ChartContainer>
      );

      expect(screen.getByText("Central Event Study")).toBeInTheDocument();
      expect(screen.getByText("Multi-horizon projections")).toBeInTheDocument();
      expect(screen.getByText("PREDICTION")).toBeInTheDocument();
      expect(screen.getByText("Chart Contents")).toBeInTheDocument();
    });

    it("renders empty and loading states correctly", () => {
      const { rerender } = render(
        <ChartContainer title="Empty Test" empty emptyMessage="No observations recorded">
          <div>Chart Content</div>
        </ChartContainer>
      );
      expect(screen.getByText("No observations recorded")).toBeInTheDocument();

      rerender(
        <ChartContainer title="Loading Test" loading>
          <div>Chart Content</div>
        </ChartContainer>
      );
      expect(screen.getByLabelText("Loading chart data")).toBeInTheDocument();
    });

    it("renders legends with non-color marker descriptions", () => {
      render(
        <ChartContainer
          title="Legend Test"
          legendItems={[
            { label: "Observed", color: "var(--chart-observed)", lineStyle: "solid" },
            { label: "Forecast", color: "var(--color-model)", lineStyle: "dashed" },
          ]}
        >
          <div>Content</div>
        </ChartContainer>
      );

      expect(screen.getByText("Observed")).toBeInTheDocument();
      expect(screen.getByText("Forecast")).toBeInTheDocument();
    });
  });

  describe("ChartTooltip", () => {
    it("renders structured items with tabular numbers when visible", () => {
      render(
        <ChartTooltip
          visible={true}
          title="T0 Announcement"
          subtitle="Day 0"
          epistemicTier="OBSERVED"
          items={[
            { label: "Return", value: "+3.45%", isNumeric: true },
            { label: "Confidence", value: "95.0%", isNumeric: true },
          ]}
          x={100}
          y={200}
        />
      );

      expect(screen.getByRole("tooltip")).toBeInTheDocument();
      expect(screen.getByText("T0 Announcement")).toBeInTheDocument();
      expect(screen.getByText("+3.45%")).toBeInTheDocument();
      expect(screen.getByText("95.0%")).toBeInTheDocument();
    });

    it("renders nothing when visible is false", () => {
      const { container } = render(
        <ChartTooltip visible={false} title="Hidden" />
      );
      expect(container.firstChild).toBeNull();
    });
  });

  describe("EventStudyChart", () => {
    const mockPoints = [
      { day: -5, label: "T-5", observedReturn: 0.012, predictedReturn: 0.01 },
      { day: -1, label: "T-1", observedReturn: 0.024, predictedReturn: 0.02 },
      { day: 0, label: "T0", observedReturn: 0.035, predictedReturn: 0.03 },
      { day: 1, label: "T+1", observedReturn: 0.041, predictedReturn: 0.042 },
      { day: 5, label: "T+5", observedReturn: 0.048, predictedReturn: 0.05 },
    ];

    it("renders SVG with observed and predicted markers", () => {
      render(<EventStudyChart points={mockPoints} title="Event Study Trajectory" />);

      expect(screen.getByRole("heading", { name: "Event Study Trajectory" })).toBeInTheDocument();
      expect(screen.getByText("Realized Abnormal Return")).toBeInTheDocument();
      expect(screen.getByText("Econometric Model Forecast")).toBeInTheDocument();
    });

    it("handles empty data gracefully", () => {
      render(<EventStudyChart points={[]} />);
      expect(screen.getByText("No econometric event study returns recorded for this pair.")).toBeInTheDocument();
    });
  });

  describe("HorizonComparisonVisualizer", () => {
    const mockComparisons = [
      {
        event_window: "[-1,+1]",
        is_modeled: true,
        predicted_direction: "POSITIVE",
        predicted_market_moving: true,
        market_moving_probability: 0.72,
        impact_score: 1.45,
        risk_score: 0.65,
        direction_probability: { POSITIVE: 0.72, NEGATIVE: 0.15, NEUTRAL: 0.13 },
      },
      {
        event_window: "[0,1]",
        is_modeled: false,
        note: "Unmodeled horizon",
      },
    ];

    it("renders modeled and unmodeled horizons with distinction", () => {
      render(<HorizonComparisonVisualizer comparisons={mockComparisons} />);

      expect(screen.getByText("[-1, +1]")).toBeInTheDocument();
      expect(screen.getByText("Unmodeled")).toBeInTheDocument();
      expect(screen.getAllByText("POSITIVE").length).toBeGreaterThan(0);
    });
  });

  describe("RiskDistributionVisualizer", () => {
    const mockDistribution = {
      VERY_LOW: 1500,
      LOW: 1200,
      MODERATE: 1000,
      HIGH: 600,
      VERY_HIGH: 400,
    };

    it("renders 5 risk bands with tabular numbers", () => {
      render(
        <RiskDistributionVisualizer
          distribution={mockDistribution}
          totalDecisions={4700}
        />
      );

      expect(screen.getByText("Very Low Risk")).toBeInTheDocument();
      expect(screen.getByText("Very High Risk")).toBeInTheDocument();
      expect(screen.getByText("1,500")).toBeInTheDocument();
      expect(screen.getByText("400")).toBeInTheDocument();
    });
  });

  describe("PreEventCarChart", () => {
    const mockSummaries = [
      {
        window: "[-30,-1]",
        mean_car: 0.0412,
        mean_mar: 0.00137,
        significant_pairs_count: 88,
        observation_count: 940,
      },
      {
        window: "[-5,-1]",
        mean_car: -0.0125,
        mean_mar: -0.0025,
        significant_pairs_count: 42,
        observation_count: 940,
      },
    ];

    it("renders CAR and MAR with sign and tabular formatting", () => {
      render(<PreEventCarChart windowSummaries={mockSummaries} />);

      expect(screen.getByText("[-30,-1]")).toBeInTheDocument();
      expect(screen.getByText("+4.12%")).toBeInTheDocument();
      expect(screen.getByText("[-5,-1]")).toBeInTheDocument();
      expect(screen.getByText("-1.25%")).toBeInTheDocument();
    });
  });
});
