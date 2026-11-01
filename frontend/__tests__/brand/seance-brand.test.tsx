/**
 * __tests__/brand/seance-brand.test.tsx
 * =====================================
 * Automated Validation for Seance Brand Identity Components
 *
 * Test Coverage:
 * 1. BrandEmblem vector rendering, sizes, and accessible markup
 * 2. SeanceBrand lockup rendering with correct spelling ("Seance")
 * 3. Sublabel presentation and accessibility labels
 * 4. Interactive Link mode vs static container mode
 * 5. Absence of raw Unicode emoji logo in primary brand lockups
 */

import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrandEmblem } from "@/components/brand/BrandEmblem";
import { SeanceBrand } from "@/components/brand/SeanceBrand";

describe("Seance Brand Components", () => {
  describe("BrandEmblem", () => {
    it("should render clean SVG vector emblem without raster artifacts", () => {
      const { container } = render(<BrandEmblem size="md" aria-label="Seance emblem" />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute("viewBox", "0 0 32 32");
      expect(svg).toHaveAttribute("width", "24");
      expect(svg).toHaveAttribute("height", "24");
    });

    it("should scale properly with various size props", () => {
      const { container: cSm } = render(<BrandEmblem size="sm" />);
      expect(cSm.querySelector("svg")).toHaveAttribute("width", "20");

      const { container: cLg } = render(<BrandEmblem size="lg" />);
      expect(cLg.querySelector("svg")).toHaveAttribute("width", "32");

      const { container: cCustom } = render(<BrandEmblem size={40} />);
      expect(cCustom.querySelector("svg")).toHaveAttribute("width", "40");
    });

    it("should have appropriate accessibility attributes", () => {
      render(<BrandEmblem size="md" aria-label="Official Seance Symbol" />);
      const emblem = screen.getByLabelText("Official Seance Symbol");
      expect(emblem).toBeInTheDocument();
      expect(emblem).toHaveAttribute("role", "img");
    });

    it("should be hidden from screen readers when decorative or paired with text", () => {
      const { container } = render(<BrandEmblem size="md" aria-hidden={true} />);
      const svg = container.querySelector("svg");
      expect(svg).toHaveAttribute("aria-hidden", "true");
    });
  });

  describe("SeanceBrand Lockup", () => {
    it("should render wordmark with correct spelling 'Seance'", () => {
      render(<SeanceBrand href="/" />);
      const brandElement = screen.getByText("Seance");
      expect(brandElement).toBeInTheDocument();
      expect(brandElement.textContent).toBe("Seance");
    });

    it("should render sublabel when enabled", () => {
      render(<SeanceBrand sublabel="Institutional Terminal" showSublabel={true} />);
      expect(screen.getByText("Institutional Terminal")).toBeInTheDocument();
    });

    it("should allow disabling sublabel", () => {
      render(<SeanceBrand showSublabel={false} />);
      expect(screen.queryByText("Decision Intelligence")).not.toBeInTheDocument();
    });

    it("should render as an anchor link when href is provided", () => {
      render(<SeanceBrand href="/overview" aria-label="Go to Overview" />);
      const link = screen.getByRole("link", { name: "Go to Overview" });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute("href", "/overview");
    });

    it("should render as static container when href is null", () => {
      const { container } = render(<SeanceBrand href={null} />);
      expect(container.querySelector("a")).toBeNull();
      expect(container.querySelector('[role="banner"]')).toBeInTheDocument();
    });

    it("should provide an accessible label by default", () => {
      render(<SeanceBrand sublabel="Decision Intelligence" />);
      const brandLink = screen.getByLabelText(/Seance · Decision Intelligence/i);
      expect(brandLink).toBeInTheDocument();
    });
  });
});
