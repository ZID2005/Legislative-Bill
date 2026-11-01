/**
 * components/layout/AppShell.tsx
 * ================================
 * Task 1.15A — Phase 2: Route-Aware Application Shell Isolation.
 *
 * Provides dedicated chrome isolation:
 * - When on `/onboarding`: Completely isolates the route from standard dashboard chrome
 *   (TopNavbar, collaboration toolbar, notification bell, dashboard theme switcher, standard breadcrumbs).
 *   Renders full-viewport content without the 56px fixed navbar top-padding.
 * - On all other routes: Renders standard TopNavbar and padded main application shell.
 */

"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { TopNavbar } from "@/components/layout/TopNavbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isOnboarding =
    pathname === "/onboarding" || (typeof pathname === "string" && pathname.startsWith("/onboarding/"));

  if (isOnboarding) {
    return (
      <main
        id="main-content"
        className="min-h-screen w-full bg-[var(--bg-base)] text-[var(--text-primary)]"
        role="main"
        tabIndex={-1}
      >
        {children}
      </main>
    );
  }

  return (
    <>
      {/* Fixed top navigation bar */}
      <TopNavbar />

      {/* Main content area — padded below navbar (56px) */}
      <main
        id="main-content"
        className="pt-14 min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)]"
        role="main"
        tabIndex={-1}
      >
        {children}
      </main>
    </>
  );
}

export default AppShell;

