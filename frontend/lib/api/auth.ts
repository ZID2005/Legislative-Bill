/**
 * lib/api/auth.ts
 * ===============
 * Authentication & Tenant Management API module.
 */

import apiClient from "@/lib/api/client";

export interface UserSession {
  user_id?: string;
  id?: string;
  email?: string;
  name?: string;
  role?: string;
  tenant_id?: string;
  [key: string]: any;
}

export interface OrganizationDetails {
  tenant_id?: string;
  name?: string;
  tier?: string;
  created_at?: string;
  [key: string]: any;
}

export interface MemberItem {
  user_id: string;
  email: string;
  name?: string;
  role: "ADMIN" | "MEMBER" | "VIEWER" | string;
  created_at?: string;
  [key: string]: any;
}

export interface AuthStatus {
  status?: string;
  mode?: string;
  external_idp?: boolean;
  [key: string]: any;
}

export const authApi = {
  login(data: FormData | Record<string, any>): Promise<any> {
    if (data instanceof FormData) {
      const email = data.get("username") || data.get("email");
      const password = data.get("password");
      const tenant_id = data.get("tenant_id");
      return apiClient.post<any>("/api/v1/auth/login", {
        email: email ? String(email) : "",
        password: password ? String(password) : undefined,
        tenant_id: tenant_id ? String(tenant_id) : undefined,
      });
    }
    return apiClient.post<any>("/api/v1/auth/login", data);
  },

  registerTenant(data: any): Promise<any> {
    return apiClient.post<any>("/api/v1/account/register", data);
  },

  logout(): Promise<any> {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_user");
      localStorage.removeItem("auth_token");
    }
    return apiClient.post<any>("/api/v1/auth/logout").catch(() => {});
  },

  getMe(): Promise<UserSession> {
    return apiClient.get<UserSession>("/api/v1/auth/me");
  },

  getStatus(): Promise<AuthStatus> {
    return apiClient.get<AuthStatus>("/api/v1/auth/status");
  },

  getOrganization(): Promise<OrganizationDetails> {
    return apiClient.get<OrganizationDetails>("/api/v1/account/organization");
  },

  listMembers(): Promise<{ items: MemberItem[]; total_members?: number }> {
    return apiClient.get<{ items: MemberItem[]; total_members?: number }>("/api/v1/account/members");
  },

  inviteMember(data: any): Promise<any> {
    return apiClient.post<any>("/api/v1/account/invite", data);
  },

  changeMemberRole(userId: string, role: string): Promise<any> {
    return apiClient.patch<any>(`/api/v1/account/members/${userId}/role`, { role });
  },

  removeMember(userId: string): Promise<any> {
    return apiClient.delete<any>(`/api/v1/account/members/${userId}`);
  },

  exportTenantData(): Promise<any> {
    return apiClient.get<any>("/api/v1/account/export");
  },

  softDeleteTenant(): Promise<any> {
    return apiClient.delete<any>("/api/v1/account/tenant");
  },
};

export default authApi;
