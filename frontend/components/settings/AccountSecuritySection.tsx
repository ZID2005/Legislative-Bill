/**
 * components/settings/AccountSecuritySection.tsx
 * ==============================================
 * Section 1: Account Identity & Cryptographic Session Security.
 *
 * Implements:
 * - User master identity (User ID, Email, Display Name, Assigned Role)
 * - Cryptographic HMAC session verification telemetry
 * - SSO / SAML connector status in evaluation mode
 * - Backend session invariants and token revocation controls
 * - Permanent sign-out action
 */

"use client";

import React from "react";
import type { UserSession, AuthStatus } from "@/lib/api/auth";

export interface AccountSecuritySectionProps {
  user: UserSession | null;
  authStatus: AuthStatus | null;
  onSignOut: () => void;
}

export function AccountSecuritySection({
  user,
  authStatus,
  onSignOut,
}: AccountSecuritySectionProps) {
  return (
    <section className="space-y-6" aria-labelledby="account-security-heading">
      {/* Section Header */}
      <div className="pb-3 border-b border-[var(--border-default)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 id="account-security-heading" className="text-base font-bold text-[var(--text-primary)] font-headline">
            Account &amp; Cryptographic Security
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            User identity credentials, HMAC session verification, and access controls.
          </p>
        </div>
        <button
          type="button"
          onClick={onSignOut}
          className="px-3.5 py-1.5 rounded-md bg-[var(--bg-secondary)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-strong)] text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors self-start sm:self-auto"
        >
          Sign Out Active Session
        </button>
      </div>

      {/* User Master Identity Card */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[var(--border-hairline)]">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline">
            User Master Identity
          </h3>
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/25">
            RBAC Enforced
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-[11px] text-[var(--text-muted)] block mb-1 font-medium">User Identifier</span>
            <div className="p-2.5 bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)] font-mono text-[var(--text-primary)] font-tabular select-all">
              {user?.user_id || "anonymous"}
            </div>
          </div>

          <div>
            <span className="text-[11px] text-[var(--text-muted)] block mb-1 font-medium">Email Address</span>
            <div className="p-2.5 bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)] text-[var(--text-primary)] truncate">
              {user?.email || "No email assigned"}
            </div>
          </div>

          <div>
            <span className="text-[11px] text-[var(--text-muted)] block mb-1 font-medium">Display Name</span>
            <div className="p-2.5 bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)] text-[var(--text-primary)]">
              {user?.display_name || "Analyst"}
            </div>
          </div>

          <div>
            <span className="text-[11px] text-[var(--text-muted)] block mb-1 font-medium">Assigned Authority Role</span>
            <div className="p-2.5 bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)] flex items-center justify-between">
              <span className="font-semibold text-blue-600 dark:text-blue-400">{user?.role || "MEMBER"}</span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono">
                Tenant: {user?.tenant_id || "default"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Identity & Access Controls */}
      <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl p-5 sm:p-6 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] font-headline pb-3 border-b border-[var(--border-hairline)]">
          Authentication Infrastructure &amp; Cryptography
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg space-y-2">
            <span className="text-[11px] text-[var(--text-muted)] block font-medium">Active Authentication Mode</span>
            <div className="font-mono text-sm text-blue-600 dark:text-blue-400 font-bold font-tabular">
              {authStatus?.auth_mode || "PRODUCTION_HMAC"}
            </div>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
              Session tokens are cryptographically hashed using HMAC-SHA256 and authenticated per-request.
            </p>
          </div>

          <div className="p-4 bg-[var(--bg-base)] border border-[var(--border-default)] rounded-lg space-y-2">
            <span className="text-[11px] text-[var(--text-muted)] block font-medium">Single Sign-On (SSO / SAML)</span>
            <div className="font-mono text-sm text-amber-600 dark:text-amber-400 font-bold font-tabular">
              {authStatus?.sso_status || "NOT_CONFIGURED"}
            </div>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
              External IdP connector is active in evaluation mode. Enterprise Okta/Azure credentials required for federated sync.
            </p>
          </div>
        </div>

        {/* Session Invariants & Revocation Notice */}
        <div className="p-4 bg-[var(--bg-base)] border border-[var(--border-hairline)] rounded-lg text-xs space-y-2">
          <span className="font-semibold text-[var(--text-secondary)] block">
            Session Invariants &amp; Token Revocation Policies:
          </span>
          <ul className="list-disc pl-5 text-[var(--text-muted)] space-y-1 text-[11px] leading-relaxed">
            <li>Signing out immediately and permanently blacklists the active session token on the backend.</li>
            <li>Spoofed developer headers (<code className="font-mono text-[var(--text-secondary)]">X-Tenant-ID / X-User-ID</code>) are strictly rejected in production mode.</li>
            <li>Session timeout: <strong className="font-tabular text-[var(--text-primary)]">{authStatus?.session_timeout_minutes || 1440} minutes</strong> of inactivity.</li>
          </ul>
        </div>
      </div>
    </section>
  );
}

export default AccountSecuritySection;

