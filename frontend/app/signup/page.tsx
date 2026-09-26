/**
 * app/signup/page.tsx
 * ===================
 * SaaS Tenant & Organization Registration.
 *
 * Task 8.19 — SaaS Launch Readiness.
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api/auth";

export default function SignupPage() {
  const router = useRouter();
  const [orgName, setOrgName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName || !ownerName || !email || !password) {
      setError("Please complete all required fields.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const resp = await authApi.registerTenant({
        organization_name: orgName.trim(),
        owner_name: ownerName.trim(),
        owner_email: email.trim().toLowerCase(),
        password: password,
      });

      // Automatically log in with new credentials
      const formData = new FormData();
      formData.append("username", email.trim().toLowerCase());
      formData.append("password", password);
      await authApi.login(formData);

      setSuccess(true);
      setTimeout(() => {
        router.push("/onboarding");
      }, 700);
    } catch (err: any) {
      setError(err.message || "Registration failed. Please check inputs and try again.");
    } finally {
      setLoading(false);
    }
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
            Create an Organization
          </h2>
          <p className="mt-2 text-center text-xs text-slate-400">
            Provision your dedicated institutional workspace and analytics partition
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800/80 rounded-lg text-xs text-red-300">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 bg-emerald-950/60 border border-emerald-800/80 rounded-lg text-xs text-emerald-300">
            Organization provisioned! Launching 8-step onboarding wizard…
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleRegister}>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="orgName">
              Organization / Fund / Institution Name
            </label>
            <input
              id="orgName"
              type="text"
              required
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="e.g. Apex Macro Capital Ltd."
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="ownerName">
              Primary Administrator / Owner Name
            </label>
            <input
              id="ownerName"
              type="text"
              required
              value={ownerName}
              onChange={(e) => setOwnerName(e.target.value)}
              placeholder="e.g. Sarah Jenkins"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

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
              placeholder="s.jenkins@apexmacro.com"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1" htmlFor="password">
              Secure Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Plan & Billing Status Disclosure */}
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div className="flex justify-between items-center text-slate-300 font-medium">
              <span>Default Plan: FREE (Evaluation)</span>
              <span className="font-mono text-[10px] text-amber-400 bg-amber-950/60 border border-amber-800/60 px-1.5 py-0.5 rounded">
                BILLING_NOT_CONNECTED
              </span>
            </div>
            <p className="text-slate-500">
              No credit card required. Full quantitative event-study library and state gazettes are instantly enabled.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || success}
            className="w-full py-2.5 px-4 border border-transparent rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors shadow-lg shadow-blue-600/30"
          >
            {loading ? "Provisioning Tenant Organization…" : "Create Organization & Continue →"}
          </button>
        </form>

        <div className="text-center text-xs text-slate-400">
          Already registered?{" "}
          <Link href="/login" className="text-blue-400 hover:text-blue-300 font-medium">
            Sign In Here
          </Link>
        </div>
      </div>
    </div>
  );
}
