/**
 * lib/api/predictions.ts
 * ========================
 * Prediction & Market Impact API client module.
 */

import apiClient from "@/lib/api/client";
import type {
  PaginatedResponse,
  PredictionDetailItem,
  PredictionSummaryItem,
} from "@/types/api";

export const predictionsApi = {
  listPredictions(params?: Record<string, any>): Promise<PaginatedResponse<PredictionSummaryItem>> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<PaginatedResponse<PredictionSummaryItem>>(`/api/v1/predictions${qs ? `?${qs}` : ""}`);
  },

  getPrediction(predictionId: string): Promise<PredictionDetailItem> {
    return apiClient.get<PredictionDetailItem>(`/api/v1/predictions/${predictionId}`);
  },

  getPredictionDecision(predictionId: string, param2?: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/predictions/${predictionId}/decision`);
  },

  compareHorizons(billIdOrPredId: string, companyIsin?: string): Promise<any> {
    const url = companyIsin
      ? `/api/v1/predictions/compare-horizons?bill_id=${billIdOrPredId}&company_isin=${companyIsin}`
      : `/api/v1/predictions/${billIdOrPredId}/horizons`;
    return apiClient.get<any>(url);
  },

  getStakeholderReport(predictionId: string, reportType?: string): Promise<any> {
    const qs = reportType ? `?report_type=${reportType}` : "";
    return apiClient.get<any>(`/api/v1/predictions/${predictionId}/stakeholder-report${qs}`);
  },

  getStakeholderReportByKey(billId: string, companyId: string, reportType?: string): Promise<any> {
    const qs = reportType ? `&report_type=${reportType}` : "";
    return apiClient.get<any>(`/api/v1/predictions/stakeholder-report?bill_id=${billId}&company_id=${companyId}${qs}`);
  },

  getTopMovers(limit = 6): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/predictions/top-movers?limit=${limit}`);
  },
};

export default predictionsApi;
