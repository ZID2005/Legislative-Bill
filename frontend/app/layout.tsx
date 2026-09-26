/**
 * app/layout.tsx
 * ==============
 * Root layout — wraps all pages with Sidebar + Header.
 * Responsive: sidebar collapses on mobile.
 */

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

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
      <body className="bg-slate-950 text-slate-200 antialiased">
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar — hidden on mobile, visible on md+ */}
          <div className="hidden md:flex md:flex-shrink-0">
            <Sidebar />
          </div>

          {/* Main content area */}
          <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
            <Header />
            <main
              id="main-content"
              className="flex-1 overflow-y-auto bg-slate-950"
              role="main"
              tabIndex={-1}
            >
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
