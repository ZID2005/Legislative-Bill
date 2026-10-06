/**
 * lib/api/bills.ts
 * ================
 * Legislative bills API client module.
 */

import apiClient from "@/lib/api/client";
import type {
  BillDetailItem,
  BillSummaryItem,
  PaginatedResponse,
} from "@/types/api";

export type ListBillsParams = Record<string, any>;

export const billsApi = {
  listBills(params?: Record<string, any>): Promise<PaginatedResponse<BillSummaryItem>> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<PaginatedResponse<BillSummaryItem>>(`/api/v1/bills${qs ? `?${qs}` : ""}`);
  },

  getBill(billId: string): Promise<BillDetailItem> {
    return apiClient.get<BillDetailItem>(`/api/v1/bills/${billId}`);
  },

  getBillPredictions(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/predictions`);
  },

  getBillCompanies(billId: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/bills/${billId}/companies`);
  },

  getBillAnticipation(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/anticipation`);
  },

  getBillPdf(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/pdf`);
  },

  getBillDossier(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/dossier`);
  },

  getBillTimeline(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/timeline`);
  },

  getBillChanges(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/changes`);
  },

  getBillPlainLanguage(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/plain-language`);
  },

  getBillStakeholders(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/stakeholders`);
  },

  getBillSectors(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/sectors`);
  },

  getBillDocuments(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/documents`);
  },

  getBillModelStatus(billId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/${billId}/model-status`);
  },

  compareBills(id1: string, id2: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/bills/compare?id1=${id1}&id2=${id2}`);
  },
};

export default billsApi;
