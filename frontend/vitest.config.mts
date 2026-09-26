/**
 * vitest.config.ts
 * ================
 * Vitest configuration for the frontend test suite.
 */

import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["__tests__/**/*.{test,spec}.{ts,tsx}"],
    pool: "forks",
    // @ts-ignore - Vitest poolOptions typing
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    fileParallelism: false,
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./"),
    },
  },
});
