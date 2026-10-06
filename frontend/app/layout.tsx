/**
 * app/layout.tsx
 * ==============
 * Task 8.25 — Root layout using new top navbar.
 * The permanent left sidebar is replaced with a top navigation system.
 * All pages are padded below the 56px fixed navbar.
 */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { TopNavbar } from "@/components/layout/TopNavbar";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "India Legislative Intelligence Platform",
    template: "%s · LegisIntel",
  },
  description:
    "India's definitive legislative intelligence and market impact prediction platform. Central Parliament bills, State legislation, corporate exposure networks, and AI-powered analysis.",
  keywords: [
    "Indian legislation",
    "parliamentary intelligence",
    "market impact",
    "legislative monitoring",
    "corporate exposure",
    "state bills",
    "NSE",
    "BSE",
  ],
  robots: {
    index: false, // SaaS — not for public indexing
    follow: false,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
      </head>
      <body className="bg-[#05090f] text-slate-200 antialiased">
        {/* Fixed top navigation bar */}
        <TopNavbar />

        {/* Main content area — padded below navbar (56px) */}
        <main
          id="main-content"
          className="pt-14 min-h-screen bg-[#05090f]"
          role="main"
          tabIndex={-1}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
