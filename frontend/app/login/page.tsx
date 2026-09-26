/**
 * app/login/page.tsx
 * ==================
 * SaaS Authentication & Tenant Sign-In.
 *
 * Task 8.19 — SaaS Launch Readiness.
 */

"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi, AuthStatus } from "@/lib/api/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    authApi.getStatus().then(setAuthStatus).catch(() => {});
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please provide both email and password.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);

      const resp = await authApi.login(formData);
      setSuccess(true);
      setTimeout(() => {
        router.push("/workspace");
      }, 500);
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  };

  const fillQuickDemo = (role: "admin" | "member") => {
    if (role === "admin") {
      setEmail("admin@example.com");
      setPassword("admin123");
    } else {
      setEmail("analyst@example.com");
      setPassword("analyst123");
    }
    setError(null);
  };

  return (
    <div className="min-h-full flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-950">
      <div className="max-w-md w-full space-y-8 bg-slate-900/80 p-8 rounded-2xl border border-slate-800 shadow-2xl backdrop-blur">
        <div>
          <div className="flex items-center justify-center gap-2 mb-2">
            <span className="text-2xl">⚖</span>
            <span className="text-xl font-bold tracking-tight text-white">LegisIntel</span>
          </div>
          <h2 className="text-center text-2xl font-extrabold text-white">
            Sign in to your organization
          </h2>
          <p className="mt-2 text-center text-xs text-slate-400">
            India Legislative Intelligence &amp; Quantitative Analytics
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800/80 rounded-lg text-xs text-red-300">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 bg-emerald-950/60 border border-emerald-800/80 rounded-lg text-xs text-emerald-300">
            Authentication successful! Launching workspace…
          </div>
        )}

        <form className="mt-8 space-y-4" onSubmit={handleLogin}>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="email">
              Work Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@institution.com"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            disabled={loading || success}
            className="w-full py-2.5 px-4 border border-transparent rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors shadow-lg shadow-blue-600/30"
          >
            {loading ? "Authenticating…" : "Sign In"}
          </button>
        </form>

        {/* Evaluation Pre-sets */}
        <div className="pt-2 border-t border-slate-800">
          <p className="text-[11px] text-slate-400 mb-2 font-medium">Quick Evaluation Sign-In:</p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => fillQuickDemo("admin")}
              className="flex-1 py-1.5 px-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-[11px] text-slate-300 transition-colors"
            >
              Default Admin
            </button>
            <button
              type="button"
              onClick={() => fillQuickDemo("member")}
              className="flex-1 py-1.5 px-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-[11px] text-slate-300 transition-colors"
            >
              Default Analyst
            </button>
          </div>
        </div>

        {/* IdP Boundary Disclosure */}
        <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
          <div className="font-semibold text-slate-300 flex items-center gap-1.5">
            <span>ℹ</span> Identity Provider Integration Boundary
          </div>
          <p>
            Mode: <span className="font-mono text-blue-400">{authStatus?.auth_mode || "INITIALIZING"}</span> ·{" "}
            SSO: <span className="font-mono text-amber-400">{authStatus?.sso_status || "NOT_CONFIGURED"}</span>
          </p>
          <p className="text-slate-500">
            Enterprise Okta / SAML / Azure AD requires external IdP credentials. Standard HMAC/PBKDF2 session auth is currently active.
          </p>
        </div>

        <div className="text-center text-xs text-slate-400">
          Need an organization account?{" "}
          <Link href="/signup" className="text-blue-400 hover:text-blue-300 font-medium">
            Register New Tenant
          </Link>
        </div>
      </div>
    </div>
  );
}
