/**
 * lib/api/risk.ts
 * ===============
 * Legislative & Market Risk API module.
 */

import apiClient from "@/lib/api/client";

export const riskApi = {
  getRiskSummary(): Promise<any> {
    return apiClient.get<any>("/api/v1/risk/summary");
  },

  listRiskBills(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/risk/bills${qs ? `?${qs}` : ""}`);
  },

  listRiskCompanies(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/risk/companies${qs ? `?${qs}` : ""}`);
  },

  analyzePortfolioRisk(body: any): Promise<any> {
    return apiClient.post<any>("/api/v1/risk/portfolio", body);
  },
};

export default riskApi;
