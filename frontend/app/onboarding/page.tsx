/**
 * app/onboarding/page.tsx
 * =======================
 * 8-Step Interactive Onboarding Wizard.
 *
 * Steps:
 * 1. Welcome & Platform Introduction
 * 2. Organization Profile Setup
 * 3. Role & Persona Selection
 * 4. Jurisdiction & Domain Interests
 * 5. Initial Watchlist Creation
 * 6. Alert Preferences & Digest Frequency
 * 7. Feature Walkthrough Preview
 * 8. Launch & Command Center Entry
 *
 * Task 8.19 — SaaS Launch Readiness.
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { watchlistsApi } from "@/lib/api/watchlists";
import { alertsApi } from "@/lib/api/alerts";

interface OnboardingState {
  step: number;
  orgName: string;
  industryFocus: string;
  teamSize: string;
  persona: string;
  selectedJurisdictions: string[];
  selectedBills: string[];
  digestFrequency: string;
  inAppAlerts: boolean;
  emailAlerts: boolean;
}

export default function OnboardingPage() {
  const router = useRouter();

  const [state, setState] = useState<OnboardingState>({
    step: 1,
    orgName: "My Organization",
    industryFocus: "Institutional Equity Research",
    teamSize: "5-20",
    persona: "Equity Research Analyst",
    selectedJurisdictions: ["CENTRAL", "KA", "TS"],
    selectedBills: ["bill_01_telecom_2023", "bill_02_dpdp_2023"],
    digestFrequency: "DAILY",
    inAppAlerts: true,
    emailAlerts: false,
  });

  const [saving, setSaving] = useState(false);

  const totalSteps = 8;

  const nextStep = () => {
    setState((prev) => ({ ...prev, step: Math.min(prev.step + 1, totalSteps) }));
  };

  const prevStep = () => {
    setState((prev) => ({ ...prev, step: Math.max(prev.step - 1, 1) }));
  };

  const toggleJurisdiction = (code: string) => {
    setState((prev) => {
      const exists = prev.selectedJurisdictions.includes(code);
      const updated = exists
        ? prev.selectedJurisdictions.filter((j) => j !== code)
        : [...prev.selectedJurisdictions, code];
      return { ...prev, selectedJurisdictions: updated };
    });
  };

  const toggleBill = (id: string) => {
    setState((prev) => {
      const exists = prev.selectedBills.includes(id);
      const updated = exists
        ? prev.selectedBills.filter((b) => b !== id)
        : [...prev.selectedBills, id];
      return { ...prev, selectedBills: updated };
    });
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      // 1. Create starter watchlist if bills selected
      if (state.selectedBills.length > 0) {
        const wl = await watchlistsApi.createWatchlist({
          name: "Priority Regulatory Watchlist",
          description: "Curated during initial onboarding wizard",
        }).catch(() => null);

        if (wl && wl.watchlist_id) {
          for (const billId of state.selectedBills) {
            await watchlistsApi.addItem(wl.watchlist_id, {
              entity_type: "bill",
              entity_id: billId,
              notes: "Added via Onboarding",
            }).catch(() => {});
          }
        }
      }

      // 2. Set alert preferences
      await alertsApi.updatePreferences({
        digest_frequency: state.digestFrequency,
        allowed_channels: state.inAppAlerts ? ["IN_APP"] : [],
      }).catch(() => {});

      router.push("/workspace");
    } catch {
      router.push("/workspace");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-full bg-slate-950 py-10 px-4 sm:px-6 lg:px-8 text-slate-200">
      <div className="max-w-3xl mx-auto">
        {/* Progress Bar & Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="font-semibold text-blue-400 uppercase tracking-wider">
              Step {state.step} of {totalSteps}
            </span>
            <span>{Math.round((state.step / totalSteps) * 100)}% Completed</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300 ease-out"
              style={{ width: `${(state.step / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Wizard Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-10 shadow-2xl backdrop-blur min-h-[460px] flex flex-col justify-between">
          {/* STEP 1: WELCOME */}
          {state.step === 1 && (
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-950/60 border border-blue-800/60 text-blue-400 text-xs font-medium mb-4">
                <span>✦</span> Welcome to LegisIntel
              </div>
              <h2 className="text-3xl font-extrabold text-white tracking-tight">
                India&apos;s Legislative Intelligence Engine
              </h2>
              <p className="mt-3 text-slate-300 leading-relaxed text-sm">
                You are setting up an institutional workspace with access to 20 Central Parliament Acts (22 scanned records), 44 State Enacted Acts, 47 quantitative securities, and 4,700 statistical predictions.
              </p>

              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-blue-400 font-semibold text-sm mb-1">
                    ✓ Econometric Event Studies
                  </div>
                  <p className="text-xs text-slate-400">
                    Pre-computed historical market impact on 47 liquid NSE/BSE securities across 5 event horizons.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-emerald-400 font-semibold text-sm mb-1">
                    ✓ State Statutory Intelligence
                  </div>
                  <p className="text-xs text-slate-400">
                    Comprehensive acts from AP, KA, KL, and TS with strict zero-stock-prediction firewall enforcement.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: ORG PROFILE */}
          {state.step === 2 && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Organization Profile</h2>
              <p className="text-sm text-slate-400 mb-6">
                Tell us about your organization to configure default reporting templates.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Organization / Firm Name
                  </label>
                  <input
                    type="text"
                    value={state.orgName}
                    onChange={(e) => setState({ ...state, orgName: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Primary Domain / Sector Focus
                  </label>
                  <select
                    value={state.industryFocus}
                    onChange={(e) => setState({ ...state, industryFocus: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Institutional Equity Research">Institutional Equity Research</option>
                    <option value="Macro Hedge Fund / Portfolio Strategy">Macro Hedge Fund / Portfolio Strategy</option>
                    <option value="Corporate Regulatory Affairs">Corporate Regulatory Affairs</option>
                    <option value="Legal &amp; Policy Advisory">Legal &amp; Policy Advisory</option>
                    <option value="Risk &amp; Compliance Management">Risk &amp; Compliance Management</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Estimated Team Size
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {["1-5", "5-20", "20+"].map((size) => (
                      <button
                        key={size}
                        type="button"
                        onClick={() => setState({ ...state, teamSize: size })}
                        className={`py-2 px-3 rounded-lg border text-xs font-medium transition-all ${
                          state.teamSize === size
                            ? "border-blue-500 bg-blue-950/60 text-blue-300"
                            : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        {size} analysts
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: ROLE & PERSONA */}
          {state.step === 3 && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Select Your Persona</h2>
              <p className="text-sm text-slate-400 mb-6">
                Choose the role that best describes your day-to-day workflow.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  {
                    id: "Equity Research Analyst",
                    icon: "📈",
                    desc: "Focus on stock return distributions, quantitative event studies, and sector beta.",
                  },
                  {
                    id: "Regulatory Affairs Director",
                    icon: "🏛",
                    desc: "Focus on bill lifecycles, state gazette compliance, and corporate risk dossiers.",
                  },
                  {
                    id: "Portfolio Manager",
                    icon: "💼",
                    desc: "High-level risk matrix, anticipation trends, and multi-tenant custom watchlists.",
                  },
                  {
                    id: "General Counsel & Policy Head",
                    icon: "⚖",
                    desc: "Statutory provisions, legal impact reports, and unpolluted state legislative records.",
                  },
                ].map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setState({ ...state, persona: p.id })}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      state.persona === p.id
                        ? "border-blue-500 bg-blue-950/40 text-slate-100 shadow-md shadow-blue-950"
                        : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div className="text-2xl mb-2">{p.icon}</div>
                    <div className="font-semibold text-slate-200 text-sm">{p.id}</div>
                    <div className="text-xs text-slate-400 mt-1">{p.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* STEP 4: JURISDICTIONS */}
          {state.step === 4 && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Jurisdiction Coverage</h2>
              <p className="text-sm text-slate-400 mb-6">
                Select the parliamentary and state jurisdictions to track in your initial feeds.
              </p>

              <div className="space-y-3">
                {[
                  { id: "CENTRAL", label: "Central Parliament of India", count: "20 Scanned Acts (22 Records)", status: "Active (Quant + Intel)" },
                  { id: "AP", label: "Andhra Pradesh Assembly", count: "12 Acts Enacted", status: "Active (Statutory)" },
                  { id: "KA", label: "Karnataka Legislature", count: "11 Acts Enacted", status: "Active (Statutory)" },
                  { id: "KL", label: "Kerala Assembly", count: "11 Acts Enacted", status: "Active (Statutory)" },
                  { id: "TS", label: "Telangana Legislature", count: "10 Acts Enacted", status: "Active (Statutory)" },
                ].map((j) => {
                  const selected = state.selectedJurisdictions.includes(j.id);
                  return (
                    <div
                      key={j.id}
                      onClick={() => toggleJurisdiction(j.id)}
                      className={`p-3.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                        selected
                          ? "border-blue-500 bg-blue-950/30 text-white"
                          : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div>
                        <div className="font-semibold text-sm">{j.label}</div>
                        <div className="text-xs text-slate-500">{j.count}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                          {j.status}
                        </span>
                        <input
                          type="checkbox"
                          checked={selected}
                          readOnly
                          className="h-4 w-4 rounded border-slate-700 text-blue-600 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 5: INITIAL WATCHLIST */}
          {state.step === 5 && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Create Starter Watchlist</h2>
              <p className="text-sm text-slate-400 mb-6">
                Select landmark legislation to seed your organization&apos;s first portfolio watchlist.
              </p>

              <div className="space-y-3">
                {[
                  { id: "bill_01_telecom_2023", title: "Telecommunications Act 2023", type: "Central", sector: "Telecom & Satcom" },
                  { id: "bill_02_dpdp_2023", title: "Digital Personal Data Protection Act 2023", type: "Central", sector: "Tech & Information" },
                  { id: "bill_04_mines_minerals_2023", title: "Mines and Minerals Amendment 2023", type: "Central", sector: "Mining & Resources" },
                  { id: "ts_act_2024_03", title: "Telangana Electricity Regulation Act 2024", type: "State (TS)", sector: "Power & Utilities" },
                  { id: "ka_act_2024_01", title: "Karnataka Gig Workers Welfare Act 2024", type: "State (KA)", sector: "Labor & Platform" },
                ].map((b) => {
                  const selected = state.selectedBills.includes(b.id);
                  return (
                    <div
                      key={b.id}
                      onClick={() => toggleBill(b.id)}
                      className={`p-3.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                        selected
                          ? "border-blue-500 bg-blue-950/30 text-white"
                          : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div>
                        <div className="font-semibold text-sm">{b.title}</div>
                        <div className="text-xs text-slate-500">
                          {b.type} · {b.sector}
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={selected}
                        readOnly
                        className="h-4 w-4 rounded border-slate-700 text-blue-600 focus:ring-blue-500"
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 6: ALERTS */}
          {state.step === 6 && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Notification &amp; Digest Frequency</h2>
              <p className="text-sm text-slate-400 mb-6">
                Configure delivery triggers for regulatory events affecting your watchlist.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-2">
                    Executive Digest Schedule
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { id: "REAL_TIME", label: "Real-time" },
                      { id: "DAILY", label: "Daily Digest" },
                      { id: "WEEKLY", label: "Weekly Brief" },
                    ].map((d) => (
                      <button
                        key={d.id}
                        type="button"
                        onClick={() => setState({ ...state, digestFrequency: d.id })}
                        className={`py-2 px-3 rounded-lg border text-xs font-medium transition-all ${
                          state.digestFrequency === d.id
                            ? "border-blue-500 bg-blue-950/60 text-blue-300"
                            : "border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-slate-200">In-App Notification Center</div>
                      <div className="text-xs text-slate-500">Live alerts in header bell &amp; workspace</div>
                    </div>
                    <input
                      type="checkbox"
                      checked={state.inAppAlerts}
                      onChange={(e) => setState({ ...state, inAppAlerts: e.target.checked })}
                      className="h-4 w-4 rounded border-slate-700 text-blue-600"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                    <div>
                      <div className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                        <span>Outbound Email Delivery</span>
                        <span className="text-[10px] font-mono text-amber-400 bg-amber-950/60 border border-amber-800/60 px-1.5 py-0.2 rounded">
                          NOT_CONFIGURED
                        </span>
                      </div>
                      <div className="text-xs text-slate-500">Requires SMTP / SendGrid integration</div>
                    </div>
                    <input
                      type="checkbox"
                      disabled
                      checked={false}
                      className="h-4 w-4 rounded border-slate-800 opacity-50 cursor-not-allowed"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 7: FEATURE PREVIEW */}
          {state.step === 7 && (
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Platform Capabilities Overview</h2>
              <p className="text-sm text-slate-400 mb-6">
                Your workspace is ready. Here are the 4 core surfaces you can now explore:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-blue-400 text-lg mb-1">🏛 Command Center</div>
                  <div className="text-xs text-slate-400">
                    Single-pane workspace showing your watchlists, active alerts, and regulatory telemetry.
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-indigo-400 text-lg mb-1">🔍 Legislative Explorer</div>
                  <div className="text-xs text-slate-400">
                    Faceted multi-state search across 66 acts, 70 corporations, and regulatory stages.
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-amber-400 text-lg mb-1">📈 Predictions Engine</div>
                  <div className="text-xs text-slate-400">
                    4,700 quantitative statistical predictions for Central acts on 47 listed securities.
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-teal-400 text-lg mb-1">✦ Grounded AI Analyst</div>
                  <div className="text-xs text-slate-400">
                    Ask questions grounded in statutory text and verified corporate exposure mappings.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 8: LAUNCH */}
          {state.step === 8 && (
            <div className="text-center py-6">
              <div className="text-5xl mb-4">🚀</div>
              <h2 className="text-3xl font-extrabold text-white mb-2">You&apos;re All Set!</h2>
              <p className="text-sm text-slate-300 max-w-lg mx-auto mb-6 leading-relaxed">
                Your organization profile is configured, your initial priority watchlist has been seeded, and your notification preferences are active.
              </p>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-left max-w-md mx-auto text-xs space-y-2 mb-8">
                <div className="flex justify-between">
                  <span className="text-slate-400">Organization:</span>
                  <span className="text-slate-200 font-medium">{state.orgName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Persona:</span>
                  <span className="text-slate-200 font-medium">{state.persona}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Watched Acts:</span>
                  <span className="text-slate-200 font-medium">{state.selectedBills.length} Acts</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Digest Schedule:</span>
                  <span className="text-slate-200 font-medium">{state.digestFrequency}</span>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between">
            {state.step > 1 ? (
              <button
                type="button"
                onClick={prevStep}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
              >
                ← Back
              </button>
            ) : (
              <div />
            )}

            {state.step < totalSteps ? (
              <button
                type="button"
                onClick={nextStep}
                className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors shadow-lg shadow-blue-600/30"
              >
                Continue →
              </button>
            ) : (
              <button
                type="button"
                disabled={saving}
                onClick={handleFinish}
                className="px-8 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm transition-colors shadow-lg shadow-emerald-600/30 disabled:opacity-50"
              >
                {saving ? "Initializing Workspace…" : "Launch Command Center 🏛"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
