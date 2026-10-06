/**
 * lib/api/monitoring.ts
 * =====================
 * Legislative monitoring API module.
 */

import apiClient from "@/lib/api/client";

export const monitoringApi = {
  getOverview(): Promise<any> {
    return apiClient.get<any>("/api/v1/monitoring/overview");
  },

  getSources(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/monitoring/sources${qs ? `?${qs}` : ""}`);
  },

  getSource(sourceId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/monitoring/sources/${sourceId}`);
  },

  getRuns(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/monitoring/runs${qs ? `?${qs}` : ""}`);
  },

  getChanges(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/monitoring/changes${qs ? `?${qs}` : ""}`);
  },

  getChangeDetail(changeId: string): Promise<any> {
    return apiClient.get<any>(`/api/v1/monitoring/changes/${changeId}`);
  },

  getSchedulerStatus(): Promise<any> {
    return apiClient.get<any>("/api/v1/monitoring/scheduler");
  },

  getStatus(): Promise<any> {
    return apiClient.get<any>("/api/v1/monitoring/status");
  },

  triggerCheck(sourceId: string): Promise<any> {
    return apiClient.post<any>(`/api/v1/monitoring/sources/${sourceId}/check`);
  },
};

export default monitoringApi;
