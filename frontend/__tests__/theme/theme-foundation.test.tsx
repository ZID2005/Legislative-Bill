/**
 * __tests__/theme/theme-foundation.test.tsx
 * =========================================
 * Automated Validation for Seance Dual-Theme Architecture
 *
 * Test Coverage:
 * 1. Default System preference initialization
 * 2. Explicit Light selection
 * 3. Explicit Dark selection
 * 4. Persistence across navigation or remounting
 * 5. Invalid stored preference handling (fallback to system)
 * 6. System preference changes while System mode is active
 * 7. Switching from System to an explicit theme
 * 8. Accessible theme-control labels & ARIA radiogroup roles
 * 9. Semantic token availability in CSS stylesheets
 */

import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider, useTheme } from "@/lib/theme/ThemeProvider";
import { ThemeSwitcher } from "@/components/theme/ThemeSwitcher";
import fs from "fs";
import path from "path";

// Test consumer component
function ThemeConsumer() {
  const { theme, resolvedTheme, setTheme, isSystem } = useTheme();
  return (
    <div>
      <span data-testid="current-theme">{theme}</span>
      <span data-testid="resolved-theme">{resolvedTheme}</span>
      <span data-testid="is-system">{String(isSystem)}</span>
      <button onClick={() => setTheme("light")}>Set Light</button>
      <button onClick={() => setTheme("dark")}>Set Dark</button>
      <button onClick={() => setTheme("system")}>Set System</button>
      <ThemeSwitcher />
    </div>
  );
}

describe("Seance Dual-Theme Architecture", () => {
  let mediaQueryListeners: Array<(e: { matches: boolean }) => void> = [];
  let isSystemDark = true;

  beforeEach(() => {
    localStorage.clear();
    mediaQueryListeners = [];
    isSystemDark = true;

    // Reset document element attributes and classes
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.classList.remove("light", "dark");

    // Mock matchMedia
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: isSystemDark,
      media: query,
      onchange: null,
      addListener: vi.fn((listener) => {
        mediaQueryListeners.push(listener);
      }),
      removeListener: vi.fn(),
      addEventListener: vi.fn((_, listener) => {
        mediaQueryListeners.push(listener);
      }),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("1. should initialize with default System preference and resolve according to OS preference", async () => {
    isSystemDark = true;
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId("current-theme").textContent).toBe("system");
    expect(screen.getByTestId("resolved-theme").textContent).toBe("dark");
    expect(screen.getByTestId("is-system").textContent).toBe("true");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("2. should support explicit Light selection and update DOM attributes", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    const lightBtn = screen.getByRole("button", { name: "Set Light" });
    await user.click(lightBtn);

    expect(screen.getByTestId("current-theme").textContent).toBe("light");
    expect(screen.getByTestId("resolved-theme").textContent).toBe("light");
    expect(screen.getByTestId("is-system").textContent).toBe("false");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(document.documentElement.classList.contains("light")).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("3. should support explicit Dark selection and update DOM attributes", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    const darkBtn = screen.getByRole("button", { name: "Set Dark" });
    await user.click(darkBtn);

    expect(screen.getByTestId("current-theme").textContent).toBe("dark");
    expect(screen.getByTestId("resolved-theme").textContent).toBe("dark");
    expect(screen.getByTestId("is-system").textContent).toBe("false");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.classList.contains("light")).toBe(false);
  });

  it("4. should persist explicit choice in localStorage across remounting", async () => {
    const user = userEvent.setup();
    const { unmount } = render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    const lightBtn = screen.getByRole("button", { name: "Set Light" });
    await user.click(lightBtn);

    expect(localStorage.getItem("seance_theme")).toBe("light");
    expect(localStorage.getItem("legisintel_theme")).toBe("light");

    unmount();

    // Re-mount new provider instance
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId("current-theme").textContent).toBe("light");
    expect(screen.getByTestId("resolved-theme").textContent).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("5. should safely handle invalid or corrupted stored preference and fallback to system", () => {
    localStorage.setItem("seance_theme", "corrupted_malicious_value_XYZ");
    isSystemDark = false; // OS is light

    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId("current-theme").textContent).toBe("system");
    expect(screen.getByTestId("resolved-theme").textContent).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("6. should dynamically follow OS preference changes when System mode is active", async () => {
    isSystemDark = true;
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId("current-theme").textContent).toBe("system");
    expect(screen.getByTestId("resolved-theme").textContent).toBe("dark");

    // Trigger OS preference change to light
    act(() => {
      mediaQueryListeners.forEach((listener) => {
        listener({ matches: false });
      });
    });

    expect(screen.getByTestId("resolved-theme").textContent).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(document.documentElement.classList.contains("light")).toBe(true);
  });

  it("7. should switch seamlessly from System to an explicit theme and back", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(screen.getByTestId("current-theme").textContent).toBe("system");

    // Switch to light
    await user.click(screen.getByRole("button", { name: "Set Light" }));
    expect(screen.getByTestId("current-theme").textContent).toBe("light");

    // Switch back to system
    await user.click(screen.getByRole("button", { name: "Set System" }));
    expect(screen.getByTestId("current-theme").textContent).toBe("system");
    expect(screen.getByTestId("is-system").textContent).toBe("true");
  });

  it("8. should provide accessible theme-control labels and ARIA radiogroup roles in ThemeSwitcher", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeSwitcher />
      </ThemeProvider>
    );

    const radiogroup = screen.getByRole("radiogroup", { name: "Theme preference" });
    expect(radiogroup).toBeInTheDocument();

    const lightRadio = screen.getByRole("radio", { name: "Light theme" });
    const darkRadio = screen.getByRole("radio", { name: "Dark theme" });
    const systemRadio = screen.getByRole("radio", { name: /System preference/i });

    expect(lightRadio).toBeInTheDocument();
    expect(darkRadio).toBeInTheDocument();
    expect(systemRadio).toBeInTheDocument();

    // Default system radio should be checked
    expect(systemRadio).toHaveAttribute("aria-checked", "true");
    expect(lightRadio).toHaveAttribute("aria-checked", "false");

    // Click light radio
    await user.click(lightRadio);
    expect(lightRadio).toHaveAttribute("aria-checked", "true");
    expect(systemRadio).toHaveAttribute("aria-checked", "false");
  });

  it("9. should define all mandatory semantic design tokens in globals.css", () => {
    const cssPath = path.resolve(__dirname, "../../app/globals.css");
    const cssContent = fs.readFileSync(cssPath, "utf-8");

    // Surface tokens
    expect(cssContent).toContain("--bg-base:");
    expect(cssContent).toContain("--surface-background:");
    expect(cssContent).toContain("--bg-surface:");
    expect(cssContent).toContain("--surface-primary:");
    expect(cssContent).toContain("--bg-card:");
    expect(cssContent).toContain("--bg-elevated:");
    expect(cssContent).toContain("--bg-nav:");
    expect(cssContent).toContain("--bg-modal:");

    // Typography tokens
    expect(cssContent).toContain("--text-primary:");
    expect(cssContent).toContain("--text-secondary:");
    expect(cssContent).toContain("--text-muted:");
    expect(cssContent).toContain("--text-link:");

    // Interaction tokens
    expect(cssContent).toContain("--action-primary:");
    expect(cssContent).toContain("--action-secondary:");
    expect(cssContent).toContain("--focus-ring:");
    expect(cssContent).toContain("--selection-bg:");

    // Borders & depth
    expect(cssContent).toContain("--border-default:");
    expect(cssContent).toContain("--border-subtle:");
    expect(cssContent).toContain("--border-strong:");
    expect(cssContent).toContain("--shadow-card:");
    expect(cssContent).toContain("--overlay-backdrop:");

    // Semantic states
    expect(cssContent).toContain("--color-positive:");
    expect(cssContent).toContain("--color-negative:");
    expect(cssContent).toContain("--color-warning:");
    expect(cssContent).toContain("--color-info:");
    expect(cssContent).toContain("--epistemic-fact-text:");
    expect(cssContent).toContain("--epistemic-prediction-text:");
    expect(cssContent).toContain("--epistemic-evidence-text:");

    // Data visualization tokens (Task 1.4)
    expect(cssContent).toContain("--chart-series-1:");
    expect(cssContent).toContain("--chart-series-6:");
    expect(cssContent).toContain("--chart-grid:");
    expect(cssContent).toContain("--chart-axis-text:");
    expect(cssContent).toContain("--chart-border:");
    expect(cssContent).toContain("--chart-tooltip-bg:");
    expect(cssContent).toContain("--chart-tooltip-text:");
    expect(cssContent).toContain("--chart-observed:");
    expect(cssContent).toContain("--chart-reference:");
    expect(cssContent).toContain("--chart-zero-line:");
    expect(cssContent).toContain("--chart-ci-band:");

    // Light theme block exists
    expect(cssContent).toContain('[data-theme="light"]');
    expect(cssContent).toContain('[data-theme="dark"]');
  });
});
