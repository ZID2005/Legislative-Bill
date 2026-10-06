/**
 * lib/api/watchlists.ts
 * =====================
 * Watchlists & Alert Rules API module.
 */

import apiClient from "@/lib/api/client";

export const watchlistsApi = {
  listWatchlists(): Promise<any[]> {
    return apiClient.get<any[]>("/api/v1/watchlists");
  },

  getWatchlist(watchlistId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/watchlists/${watchlistId}`);
  },

  createWatchlist(data: any): Promise<any> {
    return apiClient.post<any>("/api/v1/watchlists", data);
  },

  updateWatchlist(watchlistId: string, data: any): Promise<any> {
    return apiClient.put<any>(`/api/v1/watchlists/${watchlistId}`, data);
  },

  deleteWatchlist(watchlistId: string): Promise<any> {
    return apiClient.delete<any>(`/api/v1/watchlists/${watchlistId}`);
  },

  addItem(watchlistId: string, data: any): Promise<any> {
    return apiClient.post<any>(`/api/v1/watchlists/${watchlistId}/items`, data);
  },

  removeItem(watchlistId: string, itemId: string): Promise<any> {
    return apiClient.delete<any>(`/api/v1/watchlists/${watchlistId}/items/${itemId}`);
  },

  listRules(watchlistId: string): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/watchlists/${watchlistId}/rules`);
  },

  addRule(watchlistId: string, data: any): Promise<any> {
    return apiClient.post<any>(`/api/v1/watchlists/${watchlistId}/rules`, data);
  },

  updateRule(watchlistId: string, ruleId: string, data: any): Promise<any> {
    return apiClient.put<any>(`/api/v1/watchlists/${watchlistId}/rules/${ruleId}`, data);
  },

  deleteRule(watchlistId: string, ruleId: string): Promise<any> {
    return apiClient.delete<any>(`/api/v1/watchlists/${watchlistId}/rules/${ruleId}`);
  },
};

export default watchlistsApi;
