"use client";

/**
 * lib/theme/ThemeProvider.tsx
 * ===========================
 * Seance Dual-Theme Architecture Provider
 * Supports: "light" | "dark" | "system"
 *
 * Capabilities:
 * - Operating system preference detection & real-time synchronization
 * - Local storage persistence with safe validation & legacy key migration
 * - Zero-FOUC synchronization with the root inline blocking script
 * - Accessible React context for consumption by ThemeSwitcher and components
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export interface ThemeContextValue {
  theme: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: ThemePreference) => void;
  isSystem: boolean;
}

const STORAGE_KEY = "seance_theme";
const LEGACY_STORAGE_KEY = "legisintel_theme";
const ALLOWED_THEMES: readonly ThemePreference[] = ["light", "dark", "system"] as const;

export const ThemeContext = createContext<ThemeContextValue | null>(null);

function isValidTheme(value: unknown): value is ThemePreference {
  return typeof value === "string" && (ALLOWED_THEMES as readonly string[]).includes(value);
}

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined" || !window.matchMedia) {
    return "dark";
  }
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  } catch {
    return "dark";
  }
}

function getStoredTheme(): ThemePreference {
  if (typeof window === "undefined") {
    return "system";
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_STORAGE_KEY);
    if (isValidTheme(stored)) {
      return stored;
    }
  } catch {
    // LocalStorage access denied or unavailable
  }
  return "system";
}

function applyThemeToDOM(resolved: ResolvedTheme) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.setAttribute("data-theme", resolved);
  root.classList.remove("light", "dark");
  root.classList.add(resolved);
}

export interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: ThemePreference;
}

export function ThemeProvider({
  children,
  defaultTheme = "system",
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<ThemePreference>(defaultTheme);
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>("dark");
  const [mounted, setMounted] = useState(false);

  // Initialize theme from storage and detect system preference
  useEffect(() => {
    const initialStored = getStoredTheme();
    const currentSys = getSystemTheme();
    setSystemTheme(currentSys);
    setThemeState(initialStored);
    setMounted(true);

    const initialResolved = initialStored === "system" ? currentSys : initialStored;
    applyThemeToDOM(initialResolved);
  }, []);

  // Listen to OS preference changes
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;

    try {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

      const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
        const nextSys: ResolvedTheme = e.matches ? "dark" : "light";
        setSystemTheme(nextSys);
      };

      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener("change", handleChange);
      } else {
        // Legacy Safari/iOS fallback
        mediaQuery.addListener(handleChange);
      }

      return () => {
        if (mediaQuery.removeEventListener) {
          mediaQuery.removeEventListener("change", handleChange);
        } else {
          // Legacy Safari/iOS fallback
          mediaQuery.removeListener(handleChange);
        }
      };
    } catch {
      // MediaQuery not supported in environment
    }
  }, []);

  // Compute resolved theme
  const resolvedTheme: ResolvedTheme = useMemo(() => {
    if (theme === "system") {
      return systemTheme;
    }
    return theme;
  }, [theme, systemTheme]);

  // Synchronize DOM whenever resolved theme changes
  useEffect(() => {
    if (!mounted) return;
    applyThemeToDOM(resolvedTheme);
  }, [resolvedTheme, mounted]);

  // Set theme handler with validation and persistence
  const setTheme = useCallback((nextTheme: ThemePreference) => {
    const sanitizedTheme: ThemePreference = isValidTheme(nextTheme) ? nextTheme : "system";
    setThemeState(sanitizedTheme);

    try {
      localStorage.setItem(STORAGE_KEY, sanitizedTheme);
      // Keep legacy key in sync for backwards compatibility
      localStorage.setItem(LEGACY_STORAGE_KEY, sanitizedTheme);
    } catch {
      // LocalStorage access denied or full
    }

    const currentSys = getSystemTheme();
    const nextResolved = sanitizedTheme === "system" ? currentSys : sanitizedTheme;
    applyThemeToDOM(nextResolved);
  }, []);

  const value = useMemo<ThemeContextValue>(() => ({
    theme,
    resolvedTheme,
    setTheme,
    isSystem: theme === "system",
  }), [theme, resolvedTheme, setTheme]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    // Provide a safe fallback if used outside provider (e.g., during isolated component testing)
    return {
      theme: "system",
      resolvedTheme: "dark",
      setTheme: () => {},
      isSystem: true,
    };
  }
  return context;
}
