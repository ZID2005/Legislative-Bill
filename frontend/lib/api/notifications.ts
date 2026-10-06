/**
 * lib/api/notifications.ts
 * =========================
 * User notifications & digests API module.
 */

import apiClient from "@/lib/api/client";

export const notificationsApi = {
  listNotifications(params?: Record<string, any>): Promise<any> {
    const qs = params ? new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== "")
    ).toString() : "";
    return apiClient.get<any>(`/api/v1/notifications${qs ? `?${qs}` : ""}`);
  },

  getSummary(): Promise<any> {
    return apiClient.get<any>("/api/v1/notifications/summary");
  },

  getDigests(): Promise<any[]> {
    return apiClient.get<any[]>("/api/v1/notifications/digests");
  },

  markAsRead(notificationId: string): Promise<any> {
    return apiClient.post<any>(`/api/v1/notifications/${notificationId}/read`);
  },

  markAllAsRead(): Promise<any> {
    return apiClient.post<any>("/api/v1/notifications/read-all");
  },

  archive(notificationId: string): Promise<any> {
    return apiClient.post<any>(`/api/v1/notifications/${notificationId}/archive`);
  },
};

export default notificationsApi;
