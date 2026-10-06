/**
 * lib/api/industries.ts
 * =====================
 * Industry & Sector Intelligence API module.
 */

import apiClient from "@/lib/api/client";
import type { IndustryDetailItem, IndustrySummaryItem, PaginatedResponse } from "@/types/api";

export const industriesApi = {
  listIndustries(params?: Record<string, any>): Promise<PaginatedResponse<IndustrySummaryItem>> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<PaginatedResponse<IndustrySummaryItem>>(`/api/v1/industries${qs ? `?${qs}` : ""}`);
  },

  getIndustry(industryId: string): Promise<IndustryDetailItem> {
    return apiClient.get<IndustryDetailItem>(`/api/v1/industries/${industryId}`);
  },

  getIndustryBills(industryId: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/industries/${industryId}/bills`);
  },

  getIndustryCompanies(industryId: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/industries/${industryId}/companies`);
  },
};

export default industriesApi;
