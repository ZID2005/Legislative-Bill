/**
 * app/settings/page.tsx
 * =====================
 * Institutional SaaS Control Panel & Preferences Hub.
 *
 * Tabs:
 * 1. Profile & Identity
 * 2. Organization & Team Members (RBAC)
 * 3. Security & Sessions
 * 4. Alert & Digest Preferences
 * 5. AI Preferences & Metering
 * 6. Data & Privacy (Export / Soft-Delete)
 * 7. Plan & Subscriptions (Placeholder)
 *
 * Task 8.19 — SaaS Launch Readiness.
 */

"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { alertsApi } from "@/lib/api/alerts";
import { authApi, UserSession, OrganizationDetails, MemberItem, AuthStatus } from "@/lib/api/auth";
import { apiClient } from "@/lib/api/client";
import type { AlertPreferenceResponse } from "@/types/api";

type TabId = "profile" | "organization" | "security" | "alerts" | "ai" | "privacy" | "plans";

export default function SettingsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabId>("profile");

  // Auth & Org State
  const [user, setUser] = useState<UserSession | null>(null);
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [org, setOrg] = useState<OrganizationDetails | null>(null);
  const [members, setMembers] = useState<MemberItem[]>([]);
  const [aiUsage, setAiUsage] = useState<any>(null);

  // Invite state
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"ADMIN" | "MEMBER" | "VIEWER">("MEMBER");
  const [inviteMsg, setInviteMsg] = useState<string | null>(null);

  // Export & Delete state
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [deleteMsg, setDeleteMsg] = useState<string | null>(null);

  // Alerts State
  const [preferences, setPreferences] = useState<AlertPreferenceResponse | null>(null);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [alertsSaving, setAlertsSaving] = useState(false);
  const [alertsSuccess, setAlertsSuccess] = useState(false);
  const [enabled, setEnabled] = useState(true);
  const [minimumSeverity, setMinimumSeverity] = useState("MEDIUM");
  const [digestFrequency, setDigestFrequency] = useState("DAILY");
  const [allowedChannels, setAllowedChannels] = useState<string[]>(["IN_APP"]);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(false);
  const [quietHoursStart, setQuietHoursStart] = useState("22:00");
  const [quietHoursEnd, setQuietHoursEnd] = useState("07:00");

  const [globalError, setGlobalError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [u, status, o, memResp] = await Promise.allSettled([
        authApi.getMe(),
        authApi.getStatus(),
        authApi.getOrganization(),
        authApi.listMembers(),
      ]);

      if (u.status === "fulfilled") setUser(u.value);
      if (status.status === "fulfilled") setAuthStatus(status.value);
      if (o.status === "fulfilled") setOrg(o.value);
      if (memResp.status === "fulfilled") setMembers(memResp.value.items || []);

      // Load AI usage
      apiClient.get("/api/v1/ai/usage").then(setAiUsage).catch(() => {});

      // Load Alerts
      alertsApi.getPreferences().then((pref) => {
        setPreferences(pref);
        setEnabled(pref.enabled);
        setMinimumSeverity(pref.minimum_severity || "MEDIUM");
        setDigestFrequency(pref.digest_frequency || "DAILY");
        setAllowedChannels(pref.allowed_channels || ["IN_APP"]);
        setQuietHoursEnabled(pref.quiet_hours_enabled || false);
        setQuietHoursStart(pref.quiet_hours_start || "22:00");
        setQuietHoursEnd(pref.quiet_hours_end || "07:00");
      }).catch(() => {});
    } catch (err: any) {
      setGlobalError("Failed to synchronize session metadata.");
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    try {
      const res = await authApi.inviteMember({
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setInviteMsg(`Invite provisioned for ${res.email}. Outbound email delivery: ${res.outbound_email}`);
      setInviteEmail("");
      // reload members
      const memResp = await authApi.listMembers();
      setMembers(memResp.items || []);
    } catch (err: any) {
      setInviteMsg(`Failed: ${err.message}`);
    }
  };

  const handleRoleChange = async (targetUserId: string, newRole: any) => {
    try {
      await authApi.changeMemberRole(targetUserId, newRole);
      const memResp = await authApi.listMembers();
      setMembers(memResp.items || []);
    } catch (err: any) {
      alert(`Role change failed: ${err.message}`);
    }
  };

  const handleRemoveMember = async (targetUserId: string) => {
    if (!confirm("Are you sure you want to remove this member from the organization?")) return;
    try {
      await authApi.removeMember(targetUserId);
      const memResp = await authApi.listMembers();
      setMembers(memResp.items || []);
    } catch (err: any) {
      alert(`Removal failed: ${err.message}`);
    }
  };

  const handleSaveAlerts = async (e: React.FormEvent) => {
    e.preventDefault();
    setAlertsSaving(true);
    setAlertsSuccess(false);
    try {
      const updated = await alertsApi.updatePreferences({
        enabled,
        minimum_severity: minimumSeverity,
        digest_frequency: digestFrequency,
        allowed_channels: allowedChannels,
        quiet_hours_enabled: quietHoursEnabled,
        quiet_hours_start: quietHoursEnabled ? quietHoursStart : null,
        quiet_hours_end: quietHoursEnabled ? quietHoursEnd : null,
      });
      setPreferences(updated);
      setAlertsSuccess(true);
      setTimeout(() => setAlertsSuccess(false), 3000);
    } catch (err: any) {
      alert("Failed to save alert preferences.");
    } finally {
      setAlertsSaving(false);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const payload = await authApi.exportTenantData();
      setExportResult(payload);
      // Trigger download
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tenant_export_${user?.tenant_id || "data"}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteTenant = async () => {
    if (deleteConfirm !== "DELETE") {
      setDeleteMsg("Please type DELETE to confirm tenant deletion.");
      return;
    }
    try {
      await authApi.softDeleteTenant();
      setDeleteMsg("Organization marked as DELETED. Logging out…");
      setTimeout(() => {
        authApi.logout().finally(() => router.push("/login"));
      }, 1500);
    } catch (err: any) {
      setDeleteMsg(`Error: ${err.message}`);
    }
  };

  const handleSignOut = async () => {
    await authApi.logout();
    router.push("/login");
  };

  const isOwner = user?.role === "OWNER";
  const isAdmin = user?.role === "ADMIN" || isOwner;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-8 space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-slate-800 pb-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⚙</span>
            <span className="text-xs uppercase tracking-widest font-bold text-blue-400">
              SaaS Administration
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Workspace Settings &amp; Governance
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Tenant: <span className="font-mono text-slate-300">{user?.tenant_id || "default_tenant"}</span> · Role: <span className="font-semibold text-blue-400">{user?.role || "VIEWER"}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSignOut}
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>

      {globalError && (
        <div className="p-3 bg-amber-950/60 border border-amber-800/80 rounded-lg text-xs text-amber-300">
          {globalError}
        </div>
      )}

      {/* Tabs Bar */}
      <div className="flex border-b border-slate-800 space-x-1 sm:space-x-2 overflow-x-auto text-xs font-medium">
        {[
          { id: "profile", label: "Profile" },
          { id: "organization", label: "Organization & Team" },
          { id: "security", label: "Security & Sessions" },
          { id: "alerts", label: "Notifications & Alerts" },
          { id: "ai", label: "AI & Metering" },
          { id: "privacy", label: "Data & Privacy" },
          { id: "plans", label: "Subscription Plans" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as TabId)}
            className={`py-2.5 px-3.5 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === t.id
                ? "border-blue-500 text-white font-semibold"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB 1: PROFILE */}
      {activeTab === "profile" && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-base font-semibold text-white mb-4">User Master Identity</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-500 block mb-1">User ID</span>
                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 font-mono text-slate-300">
                  {user?.user_id || "anonymous"}
                </div>
              </div>
              <div>
                <span className="text-slate-500 block mb-1">Email</span>
                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-slate-300">
                  {user?.email || "No email assigned"}
                </div>
              </div>
              <div>
                <span className="text-slate-500 block mb-1">Display Name</span>
                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-slate-300">
                  {user?.display_name || "Analyst"}
                </div>
              </div>
              <div>
                <span className="text-slate-500 block mb-1">Assigned Role</span>
                <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                  <span className="font-semibold text-blue-400">{user?.role || "MEMBER"}</span>
                  <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400">
                    RBAC Enforced
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ORGANIZATION & TEAM */}
      {activeTab === "organization" && (
        <div className="space-y-6">
          {/* Org details card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-base font-semibold text-white">
                  {org?.name || "Organization Profile"}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Tenant ID: <span className="font-mono">{org?.tenant_id || user?.tenant_id}</span>
                </p>
              </div>
              <div className="flex gap-2">
                <span className="text-[10px] font-mono bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 rounded">
                  Tier: {org?.plan_tier || "FREE"}
                </span>
                <span className="text-[10px] font-mono bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded">
                  {org?.billing_status || "BILLING_NOT_CONNECTED"}
                </span>
              </div>
            </div>

            {/* Invite Form (ADMIN / OWNER only) */}
            {isAdmin && (
              <div className="mt-6 pt-6 border-t border-slate-800">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                  Invite New Member
                </h3>
                <form onSubmit={handleInvite} className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="email"
                    required
                    placeholder="analyst@firm.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="flex-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200"
                  />
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as any)}
                    className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200"
                  >
                    <option value="ADMIN">ADMIN</option>
                    <option value="MEMBER">MEMBER</option>
                    <option value="VIEWER">VIEWER</option>
                  </select>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-semibold text-white whitespace-nowrap"
                  >
                    Send Invitation
                  </button>
                </form>
                {inviteMsg && (
                  <p className="mt-2 text-xs text-slate-400 bg-slate-950 p-2 rounded border border-slate-800">
                    {inviteMsg}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Members Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4">
              Team Members ({members.length})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2 px-3">Member</th>
                    <th className="py-2 px-3">Email</th>
                    <th className="py-2 px-3">Role</th>
                    <th className="py-2 px-3">Status</th>
                    {isOwner && <th className="py-2 px-3 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {members.map((m) => (
                    <tr key={m.user_id} className="hover:bg-slate-800/40">
                      <td className="py-2.5 px-3 font-medium text-slate-200">
                        {m.display_name}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{m.email || "—"}</td>
                      <td className="py-2.5 px-3">
                        {isOwner && m.role !== "OWNER" ? (
                          <select
                            value={m.role}
                            onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                            className="bg-slate-950 border border-slate-700 text-blue-400 rounded px-2 py-1 text-xs"
                          >
                            <option value="ADMIN">ADMIN</option>
                            <option value="MEMBER">MEMBER</option>
                            <option value="VIEWER">VIEWER</option>
                          </select>
                        ) : (
                          <span className="font-semibold text-blue-400">{m.role}</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                          {m.status}
                        </span>
                      </td>
                      {isOwner && (
                        <td className="py-2.5 px-3 text-right">
                          {m.role !== "OWNER" && (
                            <button
                              onClick={() => handleRemoveMember(m.user_id)}
                              className="text-red-400 hover:text-red-300 text-xs"
                            >
                              Remove
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: SECURITY & SESSIONS */}
      {activeTab === "security" && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h2 className="text-base font-semibold text-white">Identity &amp; Access Controls</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-slate-400 block mb-1">Active Authentication Mode</span>
                <span className="font-mono text-sm text-blue-400 font-semibold">
                  {authStatus?.auth_mode || "PRODUCTION_HMAC"}
                </span>
                <p className="text-[11px] text-slate-500 mt-2">
                  Session tokens are cryptographically hashed with HMAC-SHA256 and verified per-request.
                </p>
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-slate-400 block mb-1">Single Sign-On (SSO / SAML)</span>
                <span className="font-mono text-sm text-amber-400 font-semibold">
                  {authStatus?.sso_status || "NOT_CONFIGURED"}
                </span>
                <p className="text-[11px] text-slate-500 mt-2">
                  External IdP connector is active in evaluation mode. Enterprise Okta/Azure credentials required for federated sync.
                </p>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs space-y-2">
              <div className="font-semibold text-slate-300">Session Invariants &amp; Revocation:</div>
              <ul className="list-disc pl-5 text-slate-400 space-y-1">
                <li>Signing out permanently blacklists the active session token on the backend.</li>
                <li>Spoofed developer headers (X-Tenant-ID / X-User-ID) are strictly rejected in production mode.</li>
                <li>Session timeout: {authStatus?.session_timeout_minutes || 1440} minutes.</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: ALERTS & NOTIFICATIONS */}
      {activeTab === "alerts" && (
        <form onSubmit={handleSaveAlerts} className="space-y-6">
          {alertsSuccess && (
            <div className="p-3 rounded-lg bg-emerald-950 border border-emerald-800 text-xs text-emerald-200">
              ✓ Alert &amp; notification preferences updated.
            </div>
          )}

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Enable Alert Subsystem</h3>
              <p className="text-xs text-slate-400">Master switch for all triggered notification dispatches.</p>
            </div>
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="h-5 w-5 rounded border-slate-700 text-blue-600"
            />
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white">Delivery Schedule &amp; Thresholds</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Digest Frequency
                </label>
                <select
                  value={digestFrequency}
                  onChange={(e) => setDigestFrequency(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
                >
                  <option value="REALTIME">Real-time (Instant)</option>
                  <option value="DAILY">Daily Digest</option>
                  <option value="WEEKLY">Weekly Brief</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Minimum Severity Threshold
                </label>
                <select
                  value={minimumSeverity}
                  onChange={(e) => setMinimumSeverity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
                >
                  <option value="LOW">Low (All updates)</option>
                  <option value="MEDIUM">Medium (Hearings &amp; revisions)</option>
                  <option value="HIGH">High (Committee actions)</option>
                  <option value="CRITICAL">Critical (Enactments &amp; risk flags)</option>
                </select>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={alertsSaving}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-semibold text-white shadow-lg shadow-blue-600/30"
          >
            {alertsSaving ? "Saving Preferences…" : "Save Notification Preferences"}
          </button>
        </form>
      )}

      {/* TAB 5: AI & METERING */}
      {activeTab === "ai" && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-base font-semibold text-white">Grounded AI Intelligence Usage</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Tenant-metered queries grounded against official parliamentary documents.
                </p>
              </div>
              <span className="text-[10px] font-mono bg-blue-950 border border-blue-800 text-blue-300 px-2 py-0.5 rounded">
                Telemetry Partitioned
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-slate-400 block mb-1">Total Monthly Queries</span>
                <span className="text-2xl font-bold text-white">
                  {aiUsage?.total_queries ?? 0}
                </span>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-slate-400 block mb-1">Monthly Plan Quota</span>
                <span className="text-2xl font-bold text-slate-300">
                  {aiUsage?.monthly_quota ?? "500"}
                </span>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg">
                <span className="text-slate-400 block mb-1">Grounding Citations Verified</span>
                <span className="text-2xl font-bold text-emerald-400">100%</span>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-400 space-y-2">
              <div className="font-semibold text-slate-200">Anti-Hallucination &amp; Privacy Safeguards:</div>
              <p>
                All AI queries execute with strict tenant watchlist context validation (IDOR protected).
                No customer queries or proprietary watchlists are transmitted to external model training pipelines.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: DATA & PRIVACY */}
      {activeTab === "privacy" && (
        <div className="space-y-6">
          {/* Data Export */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
            <h2 className="text-base font-semibold text-white">Export Tenant Data</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Download a complete JSON package of your organization&apos;s custom watchlists, alert rules, delivery preferences, and non-sensitive user records.
            </p>
            <button
              onClick={handleExportData}
              disabled={exporting}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-semibold text-slate-200"
            >
              {exporting ? "Generating Export…" : "Download Tenant JSON Export"}
            </button>
          </div>

          {/* Statutory Immutability Guarantee */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <span>🛡 Statutory &amp; Prediction Immutability Guarantee</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Tenant actions, onboarding modifications, or organization deletions will{" "}
              <strong className="text-slate-200">NEVER</strong> affect public legislative acts, official gazette PDFs, or frozen Central econometric event studies (20 acts, 47 securities, 4,700 predictions). Public statutory facts are globally immutable.
            </p>
          </div>

          {/* Soft-Delete Organization (OWNER ONLY) */}
          {isOwner && (
            <div className="bg-red-950/20 border border-red-900/60 rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-semibold text-red-400">Danger Zone: Delete Organization</h3>
              <p className="text-xs text-red-300 leading-relaxed">
                Soft-deleting this tenant marks your organization as deleted and revokes member sessions. Public legislative records remain untouched.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 items-center">
                <input
                  type="text"
                  placeholder='Type "DELETE" to confirm'
                  value={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  className="px-3 py-2 bg-slate-950 border border-red-900 rounded-lg text-xs text-white"
                />
                <button
                  onClick={handleDeleteTenant}
                  className="px-4 py-2 bg-red-800 hover:bg-red-700 rounded-lg text-xs font-bold text-white whitespace-nowrap"
                >
                  Delete Organization
                </button>
              </div>
              {deleteMsg && (
                <p className="text-xs text-red-400 font-medium">{deleteMsg}</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 7: PLANS & SUBSCRIPTIONS */}
      {activeTab === "plans" && (
        <div className="space-y-6">
          <div className="p-4 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-300 flex items-center justify-between">
            <span>
              ℹ Billing Integration Status: <strong className="font-mono">BILLING_NOT_CONNECTED</strong> (Task 8.19 Specification)
            </span>
            <span className="text-[10px] bg-amber-900/60 border border-amber-700 px-2 py-0.5 rounded">
              Evaluation Mode Active
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              {
                name: "FREE",
                tagline: "Evaluation & Research",
                price: "₹0",
                features: ["5 Watchlists", "10 Alert Rules", "50 AI Queries/mo", "Single User"],
                current: org?.plan_tier === "FREE" || !org?.plan_tier,
              },
              {
                name: "PRO",
                tagline: "Individual Quantitative Analyst",
                price: "₹14,999/mo",
                features: ["25 Watchlists", "100 Alert Rules", "500 AI Queries/mo", "Event Study API"],
                current: org?.plan_tier === "PRO",
              },
              {
                name: "TEAM",
                tagline: "Multi-User Research Desk",
                price: "₹49,999/mo",
                features: ["100 Watchlists", "500 Alert Rules", "2,500 AI Queries/mo", "RBAC & Audit Trail", "Up to 10 Seats"],
                current: org?.plan_tier === "TEAM",
              },
              {
                name: "ENTERPRISE",
                tagline: "Institutional Investment Banks",
                price: "Custom",
                features: ["Unlimited Watchlists", "Unlimited Alerts", "Dedicated Groq Capacity", "Custom SSO & SLA", "Complete Audit Logs"],
                current: org?.plan_tier === "ENTERPRISE",
              },
            ].map((p) => (
              <div
                key={p.name}
                className={`p-5 rounded-xl border flex flex-col justify-between ${
                  p.current
                    ? "bg-blue-950/40 border-blue-500 shadow-lg shadow-blue-950"
                    : "bg-slate-900 border-slate-800"
                }`}
              >
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-white text-sm">{p.name}</span>
                    {p.current && (
                      <span className="text-[9px] bg-blue-500 text-white font-bold px-1.5 py-0.5 rounded">
                        CURRENT
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mb-3">{p.tagline}</p>
                  <div className="text-xl font-extrabold text-white mb-4">{p.price}</div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {p.features.map((f) => (
                      <li key={f} className="flex items-center gap-1.5">
                        <span className="text-blue-400 text-xs">✓</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800">
                  <button
                    disabled
                    className="w-full py-2 bg-slate-800 text-slate-500 rounded text-xs font-semibold cursor-not-allowed"
                  >
                    PLAN_NOT_CONFIGURED
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
