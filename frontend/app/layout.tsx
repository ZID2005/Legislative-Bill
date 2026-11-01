/**
 * app/layout.tsx
 * ==============
 * Seance Root Layout
 * Integrates:
 * - Synchronous zero-FOUC theme initialization script
 * - ThemeProvider context for Light, Dark, and System modes
 * - TopNavbar with Seance branding and ThemeSwitcher
 * - Semantic design tokens for full dual-theme support
 */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { ThemeProvider } from "@/lib/theme/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "Seance · Legislative Bill Impact & Decision Intelligence",
    template: "%s · Seance",
  },
  description:
    "India's definitive legislative intelligence and market impact prediction platform. Central Parliament bills, State legislation, corporate exposure networks, and econometric decision intelligence.",
  keywords: [
    "Seance",
    "Indian legislation",
    "parliamentary intelligence",
    "market impact",
    "legislative monitoring",
    "corporate exposure",
    "state bills",
    "NSE",
    "BSE",
    "econometric event studies",
  ],
  robots: {
    index: false, // SaaS — not for public indexing
    follow: false,
  },
};

// Minimal, synchronous script evaluated before first paint to eliminate FOUC
const themeInitScript = `
(function() {
  try {
    var stored = localStorage.getItem('seance_theme') || localStorage.getItem('legisintel_theme');
    var allowed = ['light', 'dark', 'system'];
    var pref = (allowed.indexOf(stored) !== -1) ? stored : 'system';
    var isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    var resolved = (pref === 'system') ? (isDark ? 'dark' : 'light') : pref;
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.classList.remove('light', 'dark');
    document.documentElement.classList.add(resolved);
  } catch (e) {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.documentElement.classList.add('dark');
  }
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <script
          id="seance-theme-init"
          dangerouslySetInnerHTML={{ __html: themeInitScript }}
        />
      </head>
      <body className="bg-[var(--bg-base)] text-[var(--text-primary)] antialiased transition-colors duration-150">
        <ThemeProvider>
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
