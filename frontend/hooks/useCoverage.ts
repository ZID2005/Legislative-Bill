/**
 * hooks/useCoverage.ts
 * ====================
 * Hook for fetching and caching platform coverage data.
 * Used by the Overview page and coverage-aware components.
 */

"use client";

import { useApi } from "@/hooks/useApi";
import { coverageApi } from "@/lib/api/coverage";
import type { CoverageReportResponse } from "@/types/api";

export function useCoverage(): {
  coverage: CoverageReportResponse | null;
  loading: boolean;
  error: import("@/lib/errors").ApiError | null;
  refetch: () => void;
} {
  const { data, loading, error, refetch } = useApi(
    () => coverageApi.getCoverage(),
    { immediate: true }
  );

  return { coverage: data, loading, error, refetch };
}

export default useCoverage;
