/**
 * lib/api/search.ts
 * =================
 * Global search API module.
 */

import apiClient from "@/lib/api/client";
import type { SearchResponse } from "@/types/api";

export const searchApi = {
  globalSearch(q: string, limit = 20): Promise<SearchResponse> {
    const params = new URLSearchParams({ q, limit: String(limit) });
    return apiClient.get<SearchResponse>(`/api/v1/search?${params.toString()}`);
  },
};

export default searchApi;
