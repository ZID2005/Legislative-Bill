/**
 * lib/api/anticipation.ts
 * =======================
 * Market Anticipation API module.
 */

import apiClient from "@/lib/api/client";

export const anticipationApi = {
  getAnticipationSummary(): Promise<any> {
    return apiClient.get<any>("/api/v1/anticipation/summary");
  },

  listAnticipation(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/anticipation${qs ? `?${qs}` : ""}`);
  },

  getByPair(billId: string, companyIsin: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/anticipation/pair?bill_id=${billId}&company_isin=${companyIsin}`);
  },

  getPairDetail(billId: string, companyIsin: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/anticipation/pair-detail?bill_id=${billId}&company_isin=${companyIsin}`);
  },

  getEvidence(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/anticipation/evidence${qs ? `?${qs}` : ""}`);
  },

  getEvidenceById(evidenceId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/anticipation/evidence/${evidenceId}`);
  },

  getContext(billId: string, companyIsin?: string): Promise<any> {
    const qs = companyIsin ? `?bill_id=${encodeURIComponent(billId)}&company_isin=${encodeURIComponent(companyIsin)}` : `?bill_id=${encodeURIComponent(billId)}`;
    return apiClient.get<any>(`/api/v1/anticipation/context${qs}`);
  },

  getTrends(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/anticipation/trends?bill_id=${encodeURIComponent(billId)}`);
  },
};

export default anticipationApi;
