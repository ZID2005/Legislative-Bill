/**
 * lib/api/ai.ts
 * ==============
 * AI Explanation & Copilot API module.
 */

import apiClient from "@/lib/api/client";

export const aiApi = {
  ask(data: any): Promise<any> {
    return apiClient.post<any>("/api/v1/ai/ask", data);
  },

  explainBill(billId: string, operation?: string, persona?: string): Promise<any> {
    return apiClient.post<any>(`/api/v1/ai/explain/bill/${billId}`, {
      operation,
      persona,
    });
  },

  explainCompany(companyIdOrIsin: string, persona?: string): Promise<any> {
    return apiClient.post<any>(`/api/v1/ai/explain/company/${companyIdOrIsin}`, {
      persona,
    });
  },

  compare(data: any): Promise<any> {
    return apiClient.post<any>("/api/v1/ai/compare", data);
  },

  getUsage(): Promise<any> {
    return apiClient.get<any>("/api/v1/ai/usage");
  },
};

export default aiApi;
