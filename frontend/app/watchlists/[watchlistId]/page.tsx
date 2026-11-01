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
import { ErrorState, SkeletonCard } from "@/components/ui/Skeleton";

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
    if (type === "BILL") return `/bills/${encodeURIComponent(item.entity_id)}`;
    if (type === "COMPANY") return `/companies/${encodeURIComponent(item.entity_id)}`;
    if (type === "INDUSTRY") return `/industries/${encodeURIComponent(item.entity_id)}`;
    if (type === "STATE" || type === "JURISDICTION") return `/states/${encodeURIComponent(item.entity_id)}`;
    return "#";
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] p-6 sm:p-8 space-y-8">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
        <Link href="/workspace" className="hover:text-[var(--text-primary)]">
          Workspace
        </Link>
        <span>/</span>
        <Link href="/watchlists" className="hover:text-[var(--text-primary)]">
          Watchlists
        </Link>
        <span>/</span>
        <span className="text-[var(--text-primary)] font-semibold truncate max-w-xs">
          {watchlist?.name || watchlistId}
        </span>
      </div>

      {error && (
        <ErrorState error={error} onRetry={loadWatchlistDetail} />
      )}

      {loading && (
        <div className="space-y-4">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {!loading && watchlist && (
        <>
          {/* Header Banner */}
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-sm">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⭐</span>
                <h1 className="text-xl sm:text-2xl font-bold text-[var(--text-primary)]">
                  {watchlist.name}
                </h1>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                  watchlist.is_active ? "bg-[var(--color-success-bg)] text-[var(--color-success-text)] border border-[var(--color-success-border)]" : "bg-[var(--bg-elevated)] text-[var(--text-muted)]"
                }`}>
                  {watchlist.is_active ? "Active" : "Archived"}
                </span>
              </div>

              <p className="text-sm text-[var(--text-muted)] max-w-2xl leading-relaxed">
                {watchlist.description || "Custom watchlist for monitoring legislative policy and corporate exposures."}
              </p>

              <div className="flex items-center gap-4 text-xs text-[var(--text-faint)] pt-1">
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
                className="px-4 py-2 bg-[var(--bg-elevated)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] text-xs font-semibold rounded-lg border border-[var(--border-strong)] transition-colors flex items-center gap-1.5"
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
              <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
                <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
                  <span>Monitored Entities</span>
                  <span className="text-xs font-normal text-[var(--text-muted)]">
                    ({items.length} items)
                  </span>
                </h2>

                {/* Filter Tabs */}
                <div className="flex items-center gap-1 bg-[var(--bg-card)] p-1 rounded-lg border border-[var(--border-default)] text-xs">
                  {["ALL", "BILL", "COMPANY", "INDUSTRY", "STATE"].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setEntityFilter(tab)}
                      className={`px-2.5 py-1 font-medium rounded-md transition-colors ${
                        entityFilter === tab ? "bg-blue-600 text-white" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
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
                  <div
                    data-testid="empty-watchlist-items-state"
                    className="p-8 text-center bg-[var(--bg-card)]/50 rounded-xl border border-[var(--border-default)] space-y-3"
                  >
                    <div className="w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-500 flex items-center justify-center mx-auto text-base" aria-hidden="true">
                      📋
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-[var(--text-primary)]">
                        {entityFilter === "ALL" ? "No Entities in This Watchlist" : `No ${entityFilter} Entities Monitored`}
                      </h4>
                      <p className="text-xs text-[var(--text-muted)] max-w-sm mx-auto mt-0.5 leading-relaxed">
                        Add parliamentary bills, state assemblies, corporate tickers, or industry sectors to monitor regulatory milestones and trigger automated alerts.
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
                      <button
                        onClick={() => setShowAddItem(true)}
                        data-testid="add-entity-btn"
                        className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors"
                      >
                        + Add Entity Now
                      </button>
                      <Link
                        href="/bills"
                        className="px-3.5 py-1.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-default)] text-xs font-semibold transition-colors"
                      >
                        Browse Bills →
                      </Link>
                    </div>
                  </div>
                ) : (
                  filteredItems.map((it) => (
                    <div
                      key={it.item_id}
                      className="p-4 bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl hover:border-[var(--border-strong)] transition-colors flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-strong)]">
                            {it.entity_type}
                          </span>
                          <span className="text-xs font-mono text-[var(--text-muted)]">
                            {it.entity_id}
                          </span>
                        </div>
                        <h4 className="text-sm font-semibold text-[var(--text-primary)] hover:text-blue-400 transition-colors">
                          <Link href={getEntityDeepLink(it)}>
                            {it.display_name || it.entity_id}
                          </Link>
                        </h4>
                        {it.notes && (
                          <p className="text-xs text-[var(--text-muted)] italic">
                            Note: {it.notes}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Link
                          href={getEntityDeepLink(it)}
                          className="px-3 py-1.5 text-xs font-medium bg-[var(--bg-elevated)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] rounded-lg transition-colors"
                        >
                          View →
                        </Link>
                        <button
                          onClick={() => handleRemoveItem(it.item_id, it.display_name || it.entity_id)}
                          title="Remove item"
                          className="p-1.5 text-[var(--text-faint)] hover:text-red-400 rounded-lg hover:bg-[var(--bg-elevated)] transition-colors"
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
              <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
                <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
                  <span>Alert Rules</span>
                  <span className="text-xs font-normal text-[var(--text-muted)]">
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
                  <div className="p-8 text-center bg-[var(--bg-card)]/50 rounded-xl border border-[var(--border-default)] space-y-2">
                    <p className="text-xs text-[var(--text-muted)]">No alert rules attached to this watchlist.</p>
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
                      className="p-3.5 bg-[var(--bg-card)] border border-[var(--border-default)] rounded-xl space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[var(--text-primary)]">
                          {rule.alert_type}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          rule.minimum_severity === "CRITICAL"
                            ? "bg-[var(--color-danger-bg)] text-[var(--color-danger-text)] border border-[var(--color-danger-border)]"
                            : rule.minimum_severity === "HIGH"
                            ? "bg-[var(--color-warning-bg)] text-[var(--color-warning-text)] border border-[var(--color-warning-border)]"
                            : "bg-[var(--color-info-bg)] text-[var(--color-info-text)] border border-[var(--color-info-border)]"
                        }`}>
                          ≥ {rule.minimum_severity}
                        </span>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-[var(--border-default)] text-xs">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleToggleRule(rule)}
                            className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                              rule.enabled
                                ? "bg-[var(--color-success-bg)] text-[var(--color-success-text)] border border-[var(--color-success-border)]"
                                : "bg-[var(--bg-elevated)] text-[var(--text-faint)] border border-[var(--border-strong)]"
                            }`}
                          >
                            {rule.enabled ? "ENABLED" : "DISABLED"}
                          </button>
                          <span className="text-[11px] text-[var(--text-faint)]">
                            Channels: {(rule.notification_channels || []).join(", ")}
                          </span>
                        </div>

                        <button
                          onClick={() => {
                            const rid = rule.alert_rule_id || rule.rule_id;
                            if (rid) handleDeleteRule(rid);
                          }}
                          className="text-[var(--text-faint)] hover:text-red-400 text-xs"
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
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
              <h3 className="text-base font-bold text-[var(--text-primary)]">Add Monitored Entity</h3>
              <button
                onClick={() => setShowAddItem(false)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddItem} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Entity Type *
                </label>
                <select
                  value={itemType}
                  onChange={(e) => setItemType(e.target.value as any)}
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                >
                  <option value="BILL">Legislative Bill</option>
                  <option value="COMPANY">Public Company</option>
                  <option value="INDUSTRY">Industry Sector</option>
                  <option value="STATE">State Assembly</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
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
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Display Name (Optional)
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. The Coastal Shipping Bill, 2024"
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Internal Notes (Optional)
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. High priority port logistics exposure"
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddItem(false)}
                  className="px-4 py-2 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)]"
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
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-[var(--border-default)] pb-3">
              <h3 className="text-base font-bold text-[var(--text-primary)]">Attach Alert Rule</h3>
              <button
                onClick={() => setShowAddRule(false)}
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddRule} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Trigger Event Type *
                </label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value)}
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                >
                  <option value="BILL_STATUS_CHANGE">Bill Status Change (e.g. Introduced to Passed)</option>
                  <option value="NEW_EXPOSURE_DETECTED">New Corporate Exposure Detected</option>
                  <option value="RISK_LEVEL_UPGRADE">Risk Level Upgrade (e.g. to High)</option>
                  <option value="ANTICIPATION_SPIKE">Pre-Event Anticipation Signal Spike</option>
                  <option value="VERSION_CHANGE">Textual Version Modification</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Minimum Severity Threshold *
                </label>
                <select
                  value={minSeverity}
                  onChange={(e) => setMinSeverity(e.target.value)}
                  className="w-full bg-[var(--bg-base)] border border-[var(--border-strong)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
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
                  className="px-4 py-2 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)]"
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
