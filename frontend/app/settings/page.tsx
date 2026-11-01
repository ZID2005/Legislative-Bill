/**
 * app/settings/page.tsx
 * =====================
 * TASK 1.8A — SEANCE SETTINGS EXPERIENCE REDESIGN
 *
 * Implements the approved Master-Detail Institutional Governance Layout:
 * - Left Navigation (~25%): 4 Coherent Governance Sections
 *     1. Account & Security (Identity, HMAC cryptography, SSO evaluation notice, active sessions)
 *     2. Organization & Team (Tenant details, evaluation tier, invite form, RBAC member directory, plans)
 *     3. Notifications & Delivery (Alert subsystem master toggle, frequency, severity, quiet hours)
 *     4. Data Governance & Privacy (Grounded AI telemetry, JSON data export, statutory immutability, danger zone)
 * - Right Configuration Panel (~75%): Active section settings, status messages, and validation
 * - Preserves all existing APIs, permission checks (Owner/Admin/Member), validation rules, confirmation safeguards
 * - Full Light/Dark/System theme calibration and WCAG 2.2 AAA accessibility
 */

"use client";

import React, { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { alertsApi } from "@/lib/api/alerts";
import { authApi, UserSession, OrganizationDetails, MemberItem, AuthStatus } from "@/lib/api/auth";
import { apiClient } from "@/lib/api/client";
import type { AlertPreferenceResponse } from "@/types/api";

import { SettingsNav, SettingsSectionId } from "@/components/settings/SettingsNav";
import { AccountSecuritySection } from "@/components/settings/AccountSecuritySection";
import { OrganizationTeamSection } from "@/components/settings/OrganizationTeamSection";
import { NotificationsDeliverySection } from "@/components/settings/NotificationsDeliverySection";
import { DataGovernancePrivacySection } from "@/components/settings/DataGovernancePrivacySection";

function SettingsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Map incoming URL parameter (?section= or legacy ?tab=) to valid section ID
  const mapParamToSection = (param: string | null): SettingsSectionId => {
    if (!param) return "account";
    const p = param.toLowerCase();
    if (p === "account" || p === "profile" || p === "security") return "account";
    if (p === "organization" || p === "plans" || p === "team") return "organization";
    if (p === "notifications" || p === "alerts") return "notifications";
    if (p === "privacy" || p === "ai" || p === "governance") return "privacy";
    return "account";
  };

  const sectionParam = searchParams.get("section") || searchParams.get("tab");
  const [activeSection, setActiveSection] = useState<SettingsSectionId>(() =>
    mapParamToSection(sectionParam)
  );

  // Sync state if URL search param is explicitly provided
  useEffect(() => {
    if (sectionParam) {
      setActiveSection(mapParamToSection(sectionParam));
    }
  }, [sectionParam]);

  // Auth & Org State
  const [user, setUser] = useState<UserSession | null>(null);
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [org, setOrg] = useState<OrganizationDetails | null>(null);
  const [members, setMembers] = useState<MemberItem[]>([]);
  const [aiUsage, setAiUsage] = useState<any>(null);

  // Member invite state
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"ADMIN" | "MEMBER" | "VIEWER">("MEMBER");
  const [inviteMsg, setInviteMsg] = useState<string | null>(null);

  // Export & Delete state
  const [exporting, setExporting] = useState(false);
  const [, setExportResult] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [deleteMsg, setDeleteMsg] = useState<string | null>(null);

  // Alerts State
  const [, setPreferences] = useState<AlertPreferenceResponse | null>(null);
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

  const loadData = useCallback(async () => {
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

      // Load Alerts Preferences
      alertsApi
        .getPreferences()
        .then((pref) => {
          setPreferences(pref);
          setEnabled(pref.enabled);
          setMinimumSeverity(pref.minimum_severity || "MEDIUM");
          setDigestFrequency(pref.digest_frequency || "DAILY");
          setAllowedChannels(pref.allowed_channels || ["IN_APP"]);
          setQuietHoursEnabled(pref.quiet_hours_enabled || false);
          setQuietHoursStart(pref.quiet_hours_start || "22:00");
          setQuietHoursEnd(pref.quiet_hours_end || "07:00");
        })
        .catch(() => {});
    } catch {
      setGlobalError("Failed to synchronize session metadata.");
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle section switch with URL reflection
  const handleSelectSection = (sec: SettingsSectionId) => {
    setActiveSection(sec);
    const params = new URLSearchParams(window.location.search);
    params.set("section", sec);
    router.replace(`/settings?${params.toString()}`, { scroll: false });
  };

  // Invite member
  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    try {
      const res = await authApi.inviteMember({
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setInviteMsg(`Invite provisioned for ${res.email}. Outbound email delivery: ${res.outbound_email}`);
      setInviteEmail("");
      const memResp = await authApi.listMembers();
      setMembers(memResp.items || []);
    } catch (err: any) {
      setInviteMsg(`Failed: ${err.message}`);
    }
  };

  // Change member role (Owner only)
  const handleRoleChange = async (targetUserId: string, newRole: any) => {
    try {
      await authApi.changeMemberRole(targetUserId, newRole);
      const memResp = await authApi.listMembers();
      setMembers(memResp.items || []);
    } catch (err: any) {
      alert(`Role change failed: ${err.message}`);
    }
  };

  // Remove member (Owner only)
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

  // Save alerts preferences
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
    } catch {
      alert("Failed to save alert preferences.");
    } finally {
      setAlertsSaving(false);
    }
  };

  // Export tenant data
  const handleExportData = async () => {
    setExporting(true);
    try {
      const payload = await authApi.exportTenantData();
      setExportResult(payload);
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

  // Soft delete tenant
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

  // Sign out
  const handleSignOut = async () => {
    await authApi.logout();
    router.push("/login");
  };

  const isOwner = user?.role === "OWNER";
  const isAdmin = user?.role === "ADMIN" || isOwner;

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <header className="border-b border-[var(--border-default)] pb-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-base" aria-hidden="true">⚙</span>
            <span className="text-[10px] uppercase tracking-widest font-bold text-blue-500 dark:text-blue-400 font-mono">
              Institutional Administration
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25">
              Task 1.8A Grounded
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--text-primary)] font-headline">
            Workspace Settings &amp; Governance
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Tenant: <span className="font-mono text-[var(--text-secondary)] font-tabular">{user?.tenant_id || "default_tenant"}</span> · Role: <span className="font-semibold text-blue-600 dark:text-blue-400">{user?.role || "VIEWER"}</span>
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          <button
            type="button"
            onClick={handleSignOut}
            className="px-3.5 py-1.5 rounded-md bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors shadow-xs"
          >
            Sign Out Session
          </button>
        </div>
      </header>

      {globalError && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/25 rounded-lg text-xs text-amber-700 dark:text-amber-400">
          {globalError}
        </div>
      )}

      {/* Master-Detail Layout */}
      <main className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Left Navigation Sidebar (~25% / 4 Cols on md, 3 Cols on lg) */}
        <aside className="md:col-span-4 lg:col-span-3 w-full">
          <SettingsNav
            activeSection={activeSection}
            onSelectSection={handleSelectSection}
          />
        </aside>

        {/* Right Configuration Panel (~75% / 8 Cols on md, 9 Cols on lg) */}
        <section className="md:col-span-8 lg:col-span-9 w-full">
          {activeSection === "account" && (
            <AccountSecuritySection
              user={user}
              authStatus={authStatus}
              onSignOut={handleSignOut}
            />
          )}

          {activeSection === "organization" && (
            <OrganizationTeamSection
              user={user}
              org={org}
              members={members}
              isAdmin={isAdmin}
              isOwner={isOwner}
              inviteEmail={inviteEmail}
              setInviteEmail={setInviteEmail}
              inviteRole={inviteRole}
              setInviteRole={setInviteRole}
              inviteMsg={inviteMsg}
              onInvite={handleInvite}
              onRoleChange={handleRoleChange}
              onRemoveMember={handleRemoveMember}
            />
          )}

          {activeSection === "notifications" && (
            <NotificationsDeliverySection
              enabled={enabled}
              setEnabled={setEnabled}
              minimumSeverity={minimumSeverity}
              setMinimumSeverity={setMinimumSeverity}
              digestFrequency={digestFrequency}
              setDigestFrequency={setDigestFrequency}
              quietHoursEnabled={quietHoursEnabled}
              setQuietHoursEnabled={setQuietHoursEnabled}
              quietHoursStart={quietHoursStart}
              setQuietHoursStart={setQuietHoursStart}
              quietHoursEnd={quietHoursEnd}
              setQuietHoursEnd={setQuietHoursEnd}
              alertsSaving={alertsSaving}
              alertsSuccess={alertsSuccess}
              onSaveAlerts={handleSaveAlerts}
            />
          )}

          {activeSection === "privacy" && (
            <DataGovernancePrivacySection
              aiUsage={aiUsage}
              isOwner={isOwner}
              exporting={exporting}
              onExportData={handleExportData}
              deleteConfirm={deleteConfirm}
              setDeleteConfirm={setDeleteConfirm}
              deleteMsg={deleteMsg}
              onDeleteTenant={handleDeleteTenant}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--bg-base)] p-8 text-xs font-mono text-[var(--text-muted)]">Loading institutional settings…</div>}>
      <SettingsContent />
    </Suspense>
  );
}
