/**
 * __tests__/theme/visual-foundation.test.tsx
 * ==========================================
 * Automated Validation for Seance Visual Foundation & Design System (Task 1.6B)
 *
 * Verifies:
 * 1. TypeScript design tokens structure and completeness (tokens.ts & index.ts)
 * 2. 9-level Typography scale classes defined in globals.css
 * 3. Editorial serif fallback token and .font-legal styling
 * 4. Tabular numerals token and .font-tabular styling
 * 5. 8-point spatial scale and content width classes (.max-w-prose, .max-w-matrix)
 * 6. Hairline precision border utilities (.border-hairline, .hairline-t, etc.)
 * 7. Layout density classes (.density-compact, .density-standard, .density-relaxed)
 * 8. Motion tokens and prefers-reduced-motion coverage in CSS
 * 9. Button contrast safety (text-white on primary and danger)
 * 10. StatCard tabular numerals rendering
 * 11. InstitutionalTable density and tabular numerals integration
 * 12. Backward-compatibility of legacy typography classes
 */

import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import fs from "fs";
import path from "path";

import {
  fontFamilies,
  typographyScale,
  spacingScale,
  radiiScale,
  contentWidths,
  densityScale,
  motionTokens,
  epistemicColors,
  themeColors,
} from "@/lib/theme/tokens";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/Card";
import { InstitutionalTable } from "@/components/ui/InstitutionalTable";

describe("Task 1.6B — Visual Foundation & Design System", () => {
  const cssPath = path.resolve(__dirname, "../../app/globals.css");
  const cssContent = fs.readFileSync(cssPath, "utf-8");

  describe("1. TypeScript Design Tokens Integrity", () => {
    it("exports complete font family definitions including editorial serif and mono", () => {
      expect(fontFamilies.sans).toContain("Inter");
      expect(fontFamilies.serif).toContain("Newsreader");
      expect(fontFamilies.serif).toContain("Charter");
      expect(fontFamilies.mono).toContain("JetBrains Mono");
    });

    it("defines all 9 typography scale tiers with weights, line heights, and roles", () => {
      const tiers = [
        "display",
        "headline",
        "title",
        "subhead",
        "body",
        "legal",
        "tabular",
        "caption",
        "micro",
      ];
      for (const tier of tiers) {
        expect(typographyScale[tier]).toBeDefined();
        expect(typographyScale[tier].size).toBeTruthy();
        expect(typographyScale[tier].lineHeight).toBeTruthy();
        expect(typographyScale[tier].weight).toBeGreaterThan(0);
        expect(typographyScale[tier].role).toBeTruthy();
      }
      expect(typographyScale.legal.fontStyle).toBe("italic");
      expect(typographyScale.tabular.numeric).toContain("tabular-nums");
    });

    it("defines an 8-point spatial scale and restrained radii scale", () => {
      expect(spacingScale["0.5"]).toBe("0.25rem");
      expect(spacingScale["1"]).toBe("0.5rem");
      expect(spacingScale["2"]).toBe("1.0rem");
      expect(spacingScale["4"]).toBe("2.0rem");
      expect(spacingScale["8"]).toBe("4.0rem");

      expect(radiiScale.sm).toBe("4px");
      expect(radiiScale.md).toBe("6px");
      expect(radiiScale.lg).toBe("8px");
      expect(radiiScale.xl).toBe("12px");
    });

    it("defines content widths (prose, container, matrix)", () => {
      expect(contentWidths.prose).toBe("680px");
      expect(contentWidths.container).toBe("1280px");
      expect(contentWidths.matrix).toBe("1440px");
    });

    it("defines 3 layout density modes", () => {
      expect(densityScale.compact.rowHeight).toBe("36px");
      expect(densityScale.standard.rowHeight).toBe("44px");
      expect(densityScale.relaxed.lineHeight).toBe("1.65");
    });

    it("defines motion tokens and editorial easing", () => {
      expect(motionTokens.duration.fast).toBe("150ms");
      expect(motionTokens.duration.base).toBe("200ms");
      expect(motionTokens.easing.editorial).toContain("cubic-bezier");
    });

    it("defines epistemic colors for all 6 tiers in light and dark modes", () => {
      const tiers = ["FACT", "OBSERVED", "DERIVED", "INTERPRETATION", "PREDICTION", "EVIDENCE"] as const;
      for (const tier of tiers) {
        expect(epistemicColors[tier].dark.text).toBeTruthy();
        expect(epistemicColors[tier].light.text).toBeTruthy();
      }
    });

    it("defines balanced semantic colors for light and dark modes", () => {
      expect(themeColors.dark.surfaces.base).toBe("#070b12");
      expect(themeColors.light.surfaces.base).toBe("#f8fafc");
      expect(themeColors.dark.text.primary).toBe("#f8fafc");
      expect(themeColors.light.text.primary).toBe("#0f172a");
    });
  });

  describe("2. CSS Stylesheet Token Validation (globals.css)", () => {
    it("declares editorial serif variable in :root and light theme blocks", () => {
      expect(cssContent).toContain("--font-serif:");
      expect(cssContent).toContain('"Newsreader"');
      expect(cssContent).toContain('"Charter"');
    });

    it("declares 8-point spatial scale and restrained radii variables", () => {
      expect(cssContent).toContain("--space-0-5:");
      expect(cssContent).toContain("--space-1:");
      expect(cssContent).toContain("--space-2:");
      expect(cssContent).toContain("--space-4:");
      expect(cssContent).toContain("--space-8:");

      expect(cssContent).toContain("--radius-sm:");
      expect(cssContent).toContain("--radius-md:");
      expect(cssContent).toContain("--radius-lg:");
      expect(cssContent).toContain("--radius-xl:");
    });

    it("declares content width variables in CSS", () => {
      expect(cssContent).toContain("--width-prose: 680px;");
      expect(cssContent).toContain("--width-container: 1280px;");
      expect(cssContent).toContain("--width-matrix: 1440px;");
    });

    it("declares all 9 official typography scale classes", () => {
      expect(cssContent).toContain(".font-display");
      expect(cssContent).toContain(".font-headline");
      expect(cssContent).toContain(".font-title");
      expect(cssContent).toContain(".font-subhead");
      expect(cssContent).toContain(".font-body");
      expect(cssContent).toContain(".font-legal");
      expect(cssContent).toContain(".font-tabular");
      expect(cssContent).toContain(".font-caption");
      expect(cssContent).toContain(".font-micro");
    });

    it("declares hairline precision border classes and directional hairline dividers", () => {
      expect(cssContent).toContain(".border-hairline");
      expect(cssContent).toContain(".hairline-t");
      expect(cssContent).toContain(".hairline-b");
      expect(cssContent).toContain(".hairline-l");
      expect(cssContent).toContain(".hairline-r");
      expect(cssContent).toContain(".divide-hairline");
    });

    it("declares layout density utility classes", () => {
      expect(cssContent).toContain(".density-compact");
      expect(cssContent).toContain(".density-standard");
      expect(cssContent).toContain(".density-relaxed");
    });

    it("declares content width container classes", () => {
      expect(cssContent).toContain(".max-w-prose");
      expect(cssContent).toContain(".max-w-matrix");
      expect(cssContent).toContain(".container-editorial");
      expect(cssContent).toContain(".container-matrix");
    });

    it("declares subtle motion classes and respects prefers-reduced-motion", () => {
      expect(cssContent).toContain(".transition-editorial");
      expect(cssContent).toContain(".transition-subtle");
      expect(cssContent).toContain(".reveal-fade");

      // Verify reduced motion neutralizes animations
      expect(cssContent).toContain("@media (prefers-reduced-motion: reduce)");
      expect(cssContent).toContain("animation: none");
    });

    it("preserves backward-compatible legacy typography classes", () => {
      expect(cssContent).toContain(".text-display");
      expect(cssContent).toContain(".text-headline");
      expect(cssContent).toContain(".text-title");
      expect(cssContent).toContain(".text-subheading");
      expect(cssContent).toContain(".text-body");
      expect(cssContent).toContain(".text-caption");
      expect(cssContent).toContain(".text-micro");
      expect(cssContent).toContain(".font-mono-num");
      expect(cssContent).toContain(".tabular-nums");
    });
  });

  describe("3. Shared Primitive Component Compatibility", () => {
    it("Button primary and danger variants enforce text-white for high contrast in all themes", () => {
      const { rerender } = render(<Button variant="primary">Launch Workspace</Button>);
      const primaryBtn = screen.getByRole("button", { name: "Launch Workspace" });
      expect(primaryBtn).toHaveClass("text-white");
      expect(primaryBtn).toHaveClass("bg-[var(--action-primary)]");

      rerender(<Button variant="danger">Delete Watchlist</Button>);
      const dangerBtn = screen.getByRole("button", { name: "Delete Watchlist" });
      expect(dangerBtn).toHaveClass("text-white");
      expect(dangerBtn).toHaveClass("bg-[var(--color-danger)]");
    });

    it("StatCard renders numeric values with tabular lining figures", () => {
      render(
        <StatCard
          label="Tracked Securities"
          value={4700}
          subValue="+12%"
          subLabel="this session"
          trend="up"
          highlight="emerald"
        />
      );
      const valueEl = screen.getByText("4,700");
      expect(valueEl).toHaveClass("font-tabular");
      expect(valueEl).toHaveClass("tabular-nums");
    });

    it("InstitutionalTable renders numeric cells with font-tabular and tabular-nums", () => {
      const columns = [
        { key: "isin", header: "ISIN" },
        { key: "car", header: "CAR (%)", isNumeric: true },
      ];
      const data = [{ isin: "INE062A01020", car: "+2.45%" }];

      const { container } = render(
        <InstitutionalTable columns={columns} data={data} keyExtractor={(item) => item.isin} />
      );

      const numericCell = container.querySelector("td.text-right");
      expect(numericCell).toBeInTheDocument();
      expect(numericCell).toHaveClass("font-tabular");
      expect(numericCell).toHaveClass("tabular-nums");
      expect(numericCell?.textContent).toBe("+2.45%");
    });
  });
});

