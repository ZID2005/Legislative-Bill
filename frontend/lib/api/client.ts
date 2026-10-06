/**
 * lib/api/client.ts
 * =================
 * Standard HTTP client with error mapping and automatic base URL configuration.
 */

import { ApiError } from "@/lib/errors";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function buildUrl(endpoint: string): string {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return endpoint;
  }
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${BASE_URL.replace(/\/$/, "")}${cleanEndpoint}`;
}

async function request<T>(endpoint: string, init?: RequestInit): Promise<T> {
  const url = buildUrl(endpoint);
  const headers = new Headers(init?.headers);

  if (!headers.has("Content-Type") && !(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  try {
    const res = await fetch(url, {
      ...init,
      headers,
    });

    if (!res.ok) {
      let message: string | undefined;
      let userMessage: string | undefined;

      try {
        const errorData = await res.json();
        message =
          typeof errorData.detail === "string"
            ? errorData.detail
            : typeof errorData.message === "string"
            ? errorData.message
            : undefined;
        userMessage = errorData.user_message || message;
      } catch {
        // Response body not JSON
      }

      throw ApiError.fromStatus(res.status, message || userMessage);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw ApiError.network(
      err instanceof Error ? err.message : "Network request failed"
    );
  }
}

export const apiClient = {
  get<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, { method: "GET", ...options });
  },

  post<T = any>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, {
      method: "POST",
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...options,
    });
  },

  put<T = any>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, {
      method: "PUT",
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...options,
    });
  },

  patch<T = any>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, {
      method: "PATCH",
      body: data !== undefined ? JSON.stringify(data) : undefined,
      ...options,
    });
  },

  delete<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return request<T>(endpoint, { method: "DELETE", ...options });
  },
};

export default apiClient;
