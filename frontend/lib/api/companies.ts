/**
 * lib/api/companies.ts
 * =====================
 * Companies API client module.
 */

import apiClient from "@/lib/api/client";
import type {
  CompanyDetailItem,
  CompanySummaryItem,
  PaginatedResponse,
} from "@/types/api";

export const companiesApi = {
  listCompanies(params?: Record<string, any>): Promise<PaginatedResponse<CompanySummaryItem>> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<PaginatedResponse<CompanySummaryItem>>(`/api/v1/companies${qs ? `?${qs}` : ""}`);
  },

  getCompany(companyId: string): Promise<CompanyDetailItem> {
    return apiClient.get<CompanyDetailItem>(`/api/v1/companies/${companyId}`);
  },

  getCompanyPredictions(companyId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/companies/${companyId}/predictions`);
  },

  getCompanyAnticipation(companyId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/companies/${companyId}/anticipation`);
  },

  getCompanyExposures(companyId: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/companies/${companyId}/exposures`);
  },

  getCompanyBills(companyId: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/companies/${companyId}/bills`);
  },
};

export default companiesApi;
