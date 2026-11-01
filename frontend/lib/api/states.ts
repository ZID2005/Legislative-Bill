/**
 * lib/api/states.ts
 * =================
 * Typed API client for /api/v1/states endpoints.
 */

import apiClient from "@/lib/api/client";
import type { StateCoverageResponse, StateDetailResponse } from "@/types/api";

const PREFIX = "/api/v1/states";

export const statesApi = {
  /** GET /api/v1/states — State coverage overview */
  getStateCoverage(): Promise<StateCoverageResponse> {
    return apiClient.get<StateCoverageResponse>(PREFIX);
  },

  /** GET /api/v1/states/{state} — State detail dossier */
  getStateDetail(state: string): Promise<StateDetailResponse> {
    return apiClient.get<StateDetailResponse>(
      `${PREFIX}/${encodeURIComponent(state)}`
    );
  },
};

export default statesApi;
