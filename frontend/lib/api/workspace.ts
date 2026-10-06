/**
 * lib/api/workspace.ts
 * =====================
 * Personalized workspace API module.
 */

import apiClient from "@/lib/api/client";

export const workspaceApi = {
  getSummary(): Promise<any> {
    return apiClient.get<any>("/api/v1/workspace/summary");
  },

  getActivity(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/workspace/activity${qs ? `?${qs}` : ""}`);
  },

  getWatchlistActivity(): Promise<any> {
    return apiClient.get<any>("/api/v1/workspace/watchlist-activity");
  },

  getAnalyticsSnapshot(): Promise<any> {
    return apiClient.get<any>("/api/v1/workspace/analytics-snapshot");
  },

  getDigests(): Promise<any[]> {
    return apiClient.get<any[]>("/api/v1/workspace/digests");
  },

  getDecisionIntelligence(): Promise<any> {
    return apiClient.get<any>("/api/v1/workspace/decision-intelligence");
  },

  getChangeFeed(limit: number = 20): Promise<any[]> {
    return apiClient.get<any[]>(`/api/v1/workspace/change-feed?limit=${limit}`);
  },
};

export default workspaceApi;
