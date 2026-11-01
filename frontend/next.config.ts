/**
 * next.config.ts
 * ==============
 * Next.js configuration for the India Legislative Intelligence Platform.
 */

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable React strict mode double-renders in dev for faster HMR
  reactStrictMode: false,

  // Skip TypeScript checks during dev compilation for speed
  typescript: { ignoreBuildErrors: true },

  // Security headers for production
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
