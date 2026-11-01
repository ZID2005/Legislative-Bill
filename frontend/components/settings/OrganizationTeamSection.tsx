/**
 * components/settings/OrganizationTeamSection.tsx
 * ===============================================
 * Section 2: Organization Profile, Member Administration (RBAC), and Plan Tiers.
 *
 * Implements:
 * - Tenant organization profile and evaluation plan tier
 * - Member invitation form with role selection (Admin/Owner only)
 * - Team member roster with role adjustments and member removal (Owner only)
 * - Evaluation mode billing notice
 * - Subscription tier feature matrix with accurate evaluation state
 */

"use client";

import React from "react";
import type { UserSession, OrganizationDetails, MemberItem } from "@/lib/api/auth";

export interface OrganizationTeamSectionProps {
  user: UserSession | null;
  org: OrganizationDetails | null;
  members: MemberItem[];
  isAdmin: boolean;
  isOwner: boolean;
  inviteEmail: string;
  setInviteEmail: (email: string) => void;
  inviteRole: "ADMIN" | "MEMBER" | "VIEWER";
  setInviteRole: (role: "ADMIN" | "MEMBER" | "VIEWER") => void;
  inviteMsg: string | null;
  onInvite: (e: React.FormEvent) => void;
  onRoleChange: (targetUserId: string, newRole: any) => void;
  onRemoveMember: (targetUserId: string) => void;
}

export function OrganizationTeamSection({
  user,
  org,
  members,
  isAdmin,
  isOwner,
  inviteEmail,
  setInviteEmail,
  inviteRole,
  setInviteRole,
  inviteMsg,
  onInvite,
  onRoleChange,
  onRemoveMember,
}: OrganizationTeamSectionProps) {
  return (
    <section className="space-y-6" aria-labelledby="org-team-heading">
      {/* Section Header */}
      <div className="pb-3 border-b border-[var(--border-default)]">
        <h2 id="org-team-heading" className="text-base font-bold text-[var(--text-primary)] font-headline">
          Organization &amp; Team Administration
        </h2>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">
          Tenant identity, RBAC member management, and evaluation subscription tier.
        </p>
      </div>

      {/* Organization Profile Card */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 pb-3 border-b border-[var(--border-hairline)]">
          <div>
            <h3 className="text-sm font-bold text-[var(--text-primary)]">
              {org?.name || "Organization Profile"}
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Tenant ID: <span className="font-mono text-[var(--text-secondary)] font-tabular">{org?.tenant_id || user?.tenant_id}</span>
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono font-bold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/25 px-2 py-0.5 rounded-sm">
              Tier: {org?.plan_tier || "FREE"}
            </span>
            <span className="text-[10px] font-mono font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/25 px-2 py-0.5 rounded-sm">
              {org?.billing_status || "BILLING_NOT_CONNECTED"}
            </span>
          </div>
        </div>

        {/* Evaluation Mode Banner */}
        <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-xs text-amber-700 dark:text-amber-400 flex items-start gap-2.5">
          <span className="text-sm mt-0.5 select-none" aria-hidden="true">ℹ</span>
          <div className="leading-relaxed">
            <strong className="font-semibold">Evaluation Mode Notice:</strong> Billing Integration Status is currently{" "}
            <code className="font-mono text-[11px] font-bold">BILLING_NOT_CONNECTED</code>. This tenant operates in unrestricted institutional evaluation with full access to quantitative Central models and sub-national state assemblies.
          </div>
        </div>

        {/* Member Invitation Form (Admin / Owner Only) */}
        {isAdmin && (
          <div className="pt-2 space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
              Invite Team Member
            </h4>
            <form onSubmit={onInvite} className="flex flex-col sm:flex-row gap-2.5">
              <input
                type="email"
                required
                placeholder="analyst@firm.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="flex-1 px-3 py-2 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-md text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
                aria-label="New member email"
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as any)}
                className="px-3 py-2 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-md text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)] font-semibold"
                aria-label="New member role"
              >
                <option value="ADMIN">ADMIN</option>
                <option value="MEMBER">MEMBER</option>
                <option value="VIEWER">VIEWER</option>
              </select>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-md text-xs font-semibold text-white whitespace-nowrap transition-colors shadow-xs"
              >
                Send Invitation
              </button>
            </form>
            {inviteMsg && (
              <p className="text-xs text-[var(--text-muted)] bg-[var(--bg-base)] p-2.5 rounded-md border border-[var(--border-hairline)]">
                {inviteMsg}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Team Members Directory Table */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[var(--border-hairline)]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
            Team Members Directory
          </h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-[var(--bg-secondary)] border border-[var(--border-default)] text-[var(--text-muted)] font-tabular">
            {members.length} {members.length === 1 ? "Member" : "Members"}
          </span>
        </div>

        <div className="rounded-lg border border-[var(--border-default)] overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[var(--bg-base)] text-[var(--text-muted)] font-semibold border-b border-[var(--border-default)]">
              <tr>
                <th className="py-2.5 px-3">Member</th>
                <th className="py-2.5 px-3">Email</th>
                <th className="py-2.5 px-3">Role</th>
                <th className="py-2.5 px-3">Status</th>
                {isOwner && <th className="py-2.5 px-3 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-hairline)] bg-[var(--bg-card)]">
              {members.map((m) => (
                <tr key={m.user_id} className="hover:bg-[var(--bg-card-hover)]">
                  <td className="py-2.5 px-3 font-semibold text-[var(--text-primary)]">
                    {m.display_name}
                  </td>
                  <td className="py-2.5 px-3 text-[var(--text-muted)] font-mono text-[11px]">
                    {m.email || "—"}
                  </td>
                  <td className="py-2.5 px-3">
                    {isOwner && m.role !== "OWNER" ? (
                      <select
                        value={m.role}
                        onChange={(e) => onRoleChange(m.user_id, e.target.value)}
                        className="bg-[var(--bg-base)] border border-[var(--border-default)] text-blue-600 dark:text-blue-400 font-semibold rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-[var(--focus-ring)]"
                        aria-label={`Role for ${m.display_name}`}
                      >
                        <option value="ADMIN">ADMIN</option>
                        <option value="MEMBER">MEMBER</option>
                        <option value="VIEWER">VIEWER</option>
                      </select>
                    ) : (
                      <span className="font-semibold text-blue-600 dark:text-blue-400">
                        {m.role}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] border border-[var(--border-hairline)] text-[var(--text-secondary)]">
                      {m.status}
                    </span>
                  </td>
                  {isOwner && (
                    <td className="py-2.5 px-3 text-right">
                      {m.role !== "OWNER" && (
                        <button
                          type="button"
                          onClick={() => onRemoveMember(m.user_id)}
                          className="text-rose-600 dark:text-rose-400 hover:underline text-xs font-semibold focus-visible:outline-none"
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

      {/* Subscription Tier Comparison */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
        <div className="pb-3 border-b border-[var(--border-hairline)]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
            Institutional Subscription Tiers (Evaluation Reference)
          </h3>
          <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
            Self-service billing checkout is currently disabled. Contact institutional sales for enterprise SLA agreements.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
              tagline: "Individual Quant Analyst",
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
              className={`p-4 rounded-xl border flex flex-col justify-between transition-colors ${
                p.current
                  ? "bg-blue-500/5 border-blue-500/50 shadow-xs"
                  : "bg-[var(--bg-base)] border-[var(--border-default)]"
              }`}
            >
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-[var(--text-primary)] text-sm">{p.name}</span>
                  {p.current && (
                    <span className="text-[9px] bg-blue-600 text-white font-bold px-1.5 py-0.5 rounded">
                      CURRENT
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[var(--text-muted)] mb-2">{p.tagline}</p>
                <div className="text-lg font-bold font-tabular text-[var(--text-primary)] mb-3">{p.price}</div>
                <ul className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-center gap-1.5 text-[11px]">
                      <span className="text-blue-500" aria-hidden="true">✓</span> {f}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-4 pt-3 border-t border-[var(--border-hairline)]">
                <button
                  type="button"
                  disabled
                  className="w-full py-1.5 bg-[var(--bg-secondary)] text-[var(--text-muted)] rounded text-[10px] font-mono font-semibold cursor-not-allowed border border-[var(--border-hairline)]"
                >
                  PLAN_NOT_CONFIGURED
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default OrganizationTeamSection;

