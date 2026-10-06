/**
 * lib/api/coverage.ts
 * ===================
 * Coverage API client module.
 */

import apiClient from "@/lib/api/client";
import type { CoverageStatusResponse } from "@/types/api";

export const coverageApi = {
  getCoverage(): Promise<CoverageStatusResponse> {
    return apiClient.get<CoverageStatusResponse>("/api/v1/coverage");
  },
};

export default coverageApi;
