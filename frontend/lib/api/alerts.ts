/**
 * lib/api/alerts.ts
 * =================
 * Alerts API module.
 */

import apiClient from "@/lib/api/client";

export const alertsApi = {
  listAlerts(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/alerts${qs ? `?${qs}` : ""}`);
  },

  getUnreadCount(): Promise<{ unread_count: number; [key: string]: any }> {
    return apiClient.get<{ unread_count: number; [key: string]: any }>("/api/v1/alerts/unread-count");
  },

  markAsRead(alertId: string): Promise<any> {
    return apiClient.post<any>(`/api/v1/alerts/${alertId}/read`);
  },

  markAllAsRead(): Promise<any> {
    return apiClient.post<any>("/api/v1/alerts/read-all");
  },

  archive(alertId: string): Promise<any> {
    return apiClient.post<any>(`/api/v1/alerts/${alertId}/archive`);
  },

  getPreferences(): Promise<any> {
    return apiClient.get<any>("/api/v1/alerts/preferences");
  },

  updatePreferences(data: any): Promise<any> {
    return apiClient.put<any>("/api/v1/alerts/preferences", data);
  },
};

export default alertsApi;
