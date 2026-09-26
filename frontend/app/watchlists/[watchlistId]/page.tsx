/**
 * app/watchlists/[watchlistId]/page.tsx
 * =====================================
 * Watchlist Detail Workspace (Task 8.15).
 * Manage items (bills, companies, industries, states) and alert rules for a specific watchlist.
 */

"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { watchlistsApi } from "@/lib/api/watchlists";
import type {
  AlertRuleResponse,
  WatchlistItemResponse,
  WatchlistResponse,
} from "@/types/api";

interface WatchlistDetailPageProps {
  params: Promise<{ watchlistId: string }>;
}

export default function WatchlistDetailPage({ params }: WatchlistDetailPageProps) {
  const resolvedParams = use(params);
  const watchlistId = resolvedParams.watchlistId;

  const [watchlist, setWatchlist] = useState<WatchlistResponse | null>(null);
  const [items, setItems] = useState<WatchlistItemResponse[]>([]);
  const [rules, setRules] = useState<AlertRuleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter
  const [entityFilter, setEntityFilter] = useState<string>("ALL");

  // Add Item Modal
  const [showAddItem, setShowAddItem] = useState(false);
  const [itemType, setItemType] = useState<"BILL" | "COMPANY" | "INDUSTRY" | "STATE">("BILL");
  const [entityId, setEntityId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [notes, setNotes] = useState("");
  const [submittingItem, setSubmittingItem] = useState(false);

  // Add Rule Modal
  const [showAddRule, setShowAddRule] = useState(false);
  const [alertType, setAlertType] = useState("BILL_STATUS_CHANGE");
  const [minSeverity, setMinSeverity] = useState("MEDIUM");
  const [submittingRule, setSubmittingRule] = useState(false);

  const loadWatchlistDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const [wlData, rulesData] = await Promise.all([
        watchlistsApi.getWatchlist(watchlistId),
        watchlistsApi.listRules(watchlistId).catch(() => []),
      ]);
      setWatchlist(wlData);
      setItems(wlData.items || []);
      setRules(rulesData || []);
    } catch (err: unknown) {
      console.error("Failed to load watchlist:", err);
      setError("Unable to load watchlist. Please verify the watchlist exists.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWatchlistDetail();
  }, [watchlistId]);

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!entityId.trim()) return;

    setSubmittingItem(true);
    try {
      await watchlistsApi.addItem(watchlistId, {
        entity_type: itemType,
        entity_id: entityId.trim(),
        display_name: displayName.trim() || undefined,
        notes: notes.trim() || undefined,
      });
      setEntityId("");
      setDisplayName("");
      setNotes("");
      setShowAddItem(false);
      await loadWatchlistDetail();
    } catch (err: unknown) {
      console.error("Failed to add item:", err);
      alert("Failed to add entity to watchlist. Please verify the entity ID.");
    } finally {
      setSubmittingItem(false);
    }
  };

  const handleRemoveItem = async (itemId: string, name: string) => {
    if (!confirm(`Remove '${name}' from this watchlist?`)) return;

    try {
      await watchlistsApi.removeItem(watchlistId, itemId);
      await loadWatchlistDetail();
    } catch (err: unknown) {
      console.error("Failed to remove item:", err);
      alert("Failed to remove item.");
    }
  };

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingRule(true);
    try {
      await watchlistsApi.addRule(watchlistId, {
        alert_type: alertType,
        minimum_severity: minSeverity,
        notification_channels: ["IN_APP"],
        enabled: true,
      });
      setShowAddRule(false);
      await loadWatchlistDetail();
    } catch (err: unknown) {
      console.error("Failed to add alert rule:", err);
      alert("Failed to create alert rule.");
    } finally {
      setSubmittingRule(false);
    }
  };

  const handleToggleRule = async (rule: AlertRuleResponse) => {
    const ruleId = rule.alert_rule_id || rule.rule_id;
    if (!ruleId) return;
    try {
      await watchlistsApi.updateRule(watchlistId, ruleId, {
        enabled: !rule.enabled,
      });
      await loadWatchlistDetail();
    } catch (err: unknown) {
      console.error("Failed to update rule:", err);
      alert("Failed to update rule status.");
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm("Are you sure you want to delete this alert rule?")) return;
    try {
      await watchlistsApi.deleteRule(watchlistId, ruleId);
      await loadWatchlistDetail();
    } catch (err: unknown) {
      console.error("Failed to delete rule:", err);
      alert("Failed to delete rule.");
    }
  };

  const filteredItems = items.filter((item) => {
    if (entityFilter === "ALL") return true;
    return item.entity_type.toUpperCase() === entityFilter;
  });

  const getEntityDeepLink = (item: WatchlistItemResponse) => {
    const type = item.entity_type.toUpperCase();
    if (type === "BILL") return `/bills/${item.entity_id}`;
    if (type === "COMPANY") return `/companies/${item.entity_id}`;
    if (type === "INDUSTRY") return `/industries/${item.entity_id}`;
    if (type === "STATE" || type === "JURISDICTION") return `/states?state=${item.entity_id}`;
    return "#";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-8 space-y-8">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/workspace" className="hover:text-slate-200">
          Workspace
        </Link>
        <span>/</span>
        <Link href="/watchlists" className="hover:text-slate-200">
          Watchlists
        </Link>
        <span>/</span>
        <span className="text-slate-200 font-semibold truncate max-w-xs">
          {watchlist?.name || watchlistId}
        </span>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading && (
        <div className="p-12 text-center text-slate-500">Loading watchlist workspace...</div>
      )}

      {!loading && watchlist && (
        <>
          {/* Header Banner */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-sm">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⭐</span>
                <h1 className="text-xl sm:text-2xl font-bold text-slate-100">
                  {watchlist.name}
                </h1>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                  watchlist.is_active ? "bg-emerald-950 text-emerald-300 border border-emerald-800" : "bg-slate-800 text-slate-400"
                }`}>
                  {watchlist.is_active ? "Active" : "Archived"}
                </span>
              </div>

              <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
                {watchlist.description || "Custom watchlist for monitoring legislative policy and corporate exposures."}
              </p>

              <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
                <span>Created {new Date(watchlist.created_at).toLocaleDateString()}</span>
                <span>•</span>
                <span>Tenant Scoped</span>
              </div>
            </div>

            {/* Header Actions */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => setShowAddItem(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <span>+</span>
                <span>Add Entity</span>
              </button>
              <button
                onClick={() => setShowAddRule(true)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors flex items-center gap-1.5"
              >
                <span>🔔</span>
                <span>Add Alert Rule</span>
              </button>
            </div>
          </div>

          {/* Dual Grid: Monitored Entities (7 cols) + Alert Rules (5 cols) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column: Monitored Entities */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <span>Monitored Entities</span>
                  <span className="text-xs font-normal text-slate-400">
                    ({items.length} items)
                  </span>
                </h2>

                {/* Filter Tabs */}
                <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
                  {["ALL", "BILL", "COMPANY", "INDUSTRY", "STATE"].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setEntityFilter(tab)}
                      className={`px-2.5 py-1 font-medium rounded-md transition-colors ${
                        entityFilter === tab ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              {/* Items List */}
              <div className="space-y-3">
                {filteredItems.length === 0 ? (
                  <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800 space-y-2">
                    <p className="text-xs text-slate-400">No entities found for this filter.</p>
                    <button
                      onClick={() => setShowAddItem(true)}
                      className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
                    >
                      + Add an entity now
                    </button>
                  </div>
                ) : (
                  filteredItems.map((it) => (
                    <div
                      key={it.item_id}
                      className="p-4 bg-slate-900 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            {it.entity_type}
                          </span>
                          <span className="text-xs font-mono text-slate-400">
                            {it.entity_id}
                          </span>
                        </div>
                        <h4 className="text-sm font-semibold text-slate-100 hover:text-blue-400 transition-colors">
                          <Link href={getEntityDeepLink(it)}>
                            {it.display_name || it.entity_id}
                          </Link>
                        </h4>
                        {it.notes && (
                          <p className="text-xs text-slate-400 italic">
                            Note: {it.notes}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Link
                          href={getEntityDeepLink(it)}
                          className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                        >
                          View →
                        </Link>
                        <button
                          onClick={() => handleRemoveItem(it.item_id, it.display_name || it.entity_id)}
                          title="Remove item"
                          className="p-1.5 text-slate-500 hover:text-red-400 rounded-lg hover:bg-slate-800 transition-colors"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Column: Alert Rules */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <span>Alert Rules</span>
                  <span className="text-xs font-normal text-slate-400">
                    ({rules.length} active triggers)
                  </span>
                </h2>

                <button
                  onClick={() => setShowAddRule(true)}
                  className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
                >
                  + Add Rule
                </button>
              </div>

              {/* Rules List */}
              <div className="space-y-3">
                {rules.length === 0 ? (
                  <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800 space-y-2">
                    <p className="text-xs text-slate-400">No alert rules attached to this watchlist.</p>
                    <button
                      onClick={() => setShowAddRule(true)}
                      className="text-xs text-blue-400 hover:text-blue-300 font-semibold"
                    >
                      + Create trigger rule
                    </button>
                  </div>
                ) : (
                  rules.map((rule) => (
                    <div
                      key={rule.rule_id}
                      className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-200">
                          {rule.alert_type}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          rule.minimum_severity === "CRITICAL"
                            ? "bg-red-950 text-red-300 border border-red-800"
                            : rule.minimum_severity === "HIGH"
                            ? "bg-amber-950 text-amber-300 border border-amber-800"
                            : "bg-blue-950 text-blue-300 border border-blue-800"
                        }`}>
                          ≥ {rule.minimum_severity}
                        </span>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleToggleRule(rule)}
                            className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                              rule.enabled
                                ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                : "bg-slate-800 text-slate-500 border border-slate-700"
                            }`}
                          >
                            {rule.enabled ? "ENABLED" : "DISABLED"}
                          </button>
                          <span className="text-[11px] text-slate-500">
                            Channels: {(rule.notification_channels || []).join(", ")}
                          </span>
                        </div>

                        <button
                          onClick={() => {
                            const rid = rule.alert_rule_id || rule.rule_id;
                            if (rid) handleDeleteRule(rid);
                          }}
                          className="text-slate-500 hover:text-red-400 text-xs"
                          title="Delete Rule"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Add Item Modal */}
      {showAddItem && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100">Add Monitored Entity</h3>
              <button
                onClick={() => setShowAddItem(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddItem} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Entity Type *
                </label>
                <select
                  value={itemType}
                  onChange={(e) => setItemType(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                >
                  <option value="BILL">Legislative Bill</option>
                  <option value="COMPANY">Public Company</option>
                  <option value="INDUSTRY">Industry Sector</option>
                  <option value="STATE">State Assembly</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Entity ID / Symbol *
                </label>
                <input
                  type="text"
                  required
                  value={entityId}
                  onChange={(e) => setEntityId(e.target.value)}
                  placeholder={
                    itemType === "BILL"
                      ? "e.g. the-coastal-shipping-bill-2024"
                      : itemType === "COMPANY"
                      ? "e.g. INE758T01015"
                      : itemType === "INDUSTRY"
                      ? "e.g. renewable_energy"
                      : "e.g. Maharashtra"
                  }
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Display Name (Optional)
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. The Coastal Shipping Bill, 2024"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Internal Notes (Optional)
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. High priority port logistics exposure"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddItem(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingItem || !entityId.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  {submittingItem ? "Adding..." : "Add to Watchlist"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Alert Rule Modal */}
      {showAddRule && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100">Attach Alert Rule</h3>
              <button
                onClick={() => setShowAddRule(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddRule} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Trigger Event Type *
                </label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                >
                  <option value="BILL_STATUS_CHANGE">Bill Status Change (e.g. Introduced to Passed)</option>
                  <option value="NEW_EXPOSURE_DETECTED">New Corporate Exposure Detected</option>
                  <option value="RISK_LEVEL_UPGRADE">Risk Level Upgrade (e.g. to High)</option>
                  <option value="ANTICIPATION_SPIKE">Pre-Event Anticipation Signal Spike</option>
                  <option value="VERSION_CHANGE">Textual Version Modification</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Minimum Severity Threshold *
                </label>
                <select
                  value={minSeverity}
                  onChange={(e) => setMinSeverity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                >
                  <option value="LOW">Low (All updates)</option>
                  <option value="MEDIUM">Medium (Default - Substantive changes)</option>
                  <option value="HIGH">High (Major legislative movement)</option>
                  <option value="CRITICAL">Critical (Passed / Enacted / High Risk only)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddRule(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingRule}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  {submittingRule ? "Attaching..." : "Attach Rule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
