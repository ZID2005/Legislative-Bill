/**
 * next.config.ts
 * ==============
 * Next.js configuration for the India Legislative Intelligence Platform.
 */

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Strict mode for catching common React mistakes
  reactStrictMode: true,

  // Environment variables documentation
  // NEXT_PUBLIC_API_BASE_URL must be set in .env.local

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
