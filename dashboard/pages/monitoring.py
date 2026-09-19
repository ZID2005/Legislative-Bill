"""
dashboard/pages/monitoring.py
==============================
Legislative Monitoring Dashboard Page (QA / Admin Interface).

Displays:
- Monitoring system status (enabled/disabled, scheduler state)
- Last run summary (status, timestamp, new bills, changes)
- Source status table (all sources, enabled/disabled, last checked)
- Recent notification events feed
- "Check Now" manual trigger button

This is a QA/admin interface only. The final polished SaaS frontend
will be built in a later task.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is accessible
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st


def render_monitoring_page() -> None:
    """Render the Legislative Monitoring QA/Admin dashboard page."""
    st.title("🔭 Legislative Monitoring System")
    st.caption("Task 8.11 — QA & Admin Interface | Real-time legislative update monitoring")
    st.markdown("---")

    # Lazy import to avoid heavy loading on other pages
    try:
        from services.monitoring.scheduler import LegislativeScheduler, SchedulerConfig
        from services.monitoring.source_registry import MonitoringSourceRegistry
        from services.monitoring.monitoring_runner import MonitoringRunner
        from services.monitoring.notification_events import LegislativeEventFeed
        from storage.monitoring_repository import MonitoringRepository
        _monitoring_available = True
    except ImportError as e:
        st.error(f"⚠️ Monitoring module unavailable: {e}")
        return

    # -- Status Panel --
    col1, col2, col3, col4 = st.columns(4)

    try:
        config = SchedulerConfig()
        registry = MonitoringSourceRegistry()
        repo = MonitoringRepository()
        feed = LegislativeEventFeed()
        last_run = repo.get_last_run()

        with col1:
            enabled_label = "✅ Enabled" if config.enabled else "⏸️ Disabled"
            st.metric("Scheduler", enabled_label)

        with col2:
            enabled_sources = registry.get_enabled()
            st.metric("Enabled Sources", len(enabled_sources))

        with col3:
            if last_run:
                status_icon = "✅" if last_run.status.value == "SUCCESS" else "⚠️" if "PARTIAL" in last_run.status.value else "❌"
                st.metric("Last Run Status", f"{status_icon} {last_run.status.value}")
            else:
                st.metric("Last Run Status", "No runs yet")

        with col4:
            event_count = feed.get_event_count()
            st.metric("Total Events", event_count)

    except Exception as e:
        st.error(f"Could not load monitoring status: {e}")
        return

    st.markdown("---")

    # -- Scheduler Configuration --
    with st.expander("⚙️ Scheduler Configuration", expanded=False):
        try:
            cfg = config.to_dict()
            cols = st.columns(3)
            cols[0].metric("Central Interval", f"{cfg['central_interval_hours']}h")
            cols[1].metric("State Interval", f"{cfg['state_interval_hours']}h")
            cols[2].metric("Max Retries", cfg['max_retries'])
            st.caption(
                "Configure via environment variables: `LEGISLATIVE_MONITOR_ENABLED`, "
                "`CENTRAL_MONITOR_INTERVAL`, `STATE_MONITOR_INTERVAL`, "
                "`MONITOR_MAX_RETRIES`, `MONITOR_TIMEOUT`"
            )
        except Exception as e:
            st.warning(f"Could not load config: {e}")

    # -- Manual Check Now --
    st.subheader("🔄 Manual Update Check")
    st.caption(
        "Trigger an immediate check across all enabled legislative sources. "
        "One failed source will not prevent others from being checked."
    )

    if st.button("🔄 Check for Legislative Updates Now", key="btn_check_now", type="primary"):
        with st.spinner("Running legislative update check..."):
            try:
                runner = MonitoringRunner(
                    source_registry=registry,
                    monitoring_repo=repo,
                    event_feed=feed,
                )
                result = runner.run_once(trigger="manual")
                _display_run_result(result)
            except Exception as e:
                st.error(f"Monitoring run failed: {e}")

    # -- Last Run Details --
    if last_run:
        st.subheader("📋 Last Monitoring Run")
        _display_run_result(last_run.to_dict())

    st.markdown("---")

    # -- Source Status Table --
    st.subheader("🌐 Source Status")
    _render_source_table(registry)

    st.markdown("---")

    # -- Recent Events Feed --
    st.subheader("📡 Recent Legislative Events")
    _render_events_feed(feed)

    # -- Baseline Protection Note --
    st.markdown("---")
    with st.expander("🛡️ Data Protection Guarantees", expanded=False):
        st.markdown("""
        **The monitoring system enforces strict data protection:**
        
        | Protection | Status |
        |---|---|
        | State predictions | Always EXACTLY 0 |
        | Central training data | Never modified by monitoring |
        | Central predictions (4,700) | Never modified by monitoring |
        | Backtesting records | Never modified by monitoring |
        | Historical data | Always preserved |
        | Audit trail | Always maintained |
        
        **Current automated legislative monitoring covers:**
        - ✅ Central Government (Lok Sabha, Rajya Sabha, PRS)
        - ✅ Andhra Pradesh Legislature
        - ✅ Karnataka Legislative Assembly  
        - ✅ Kerala Niyamasabha
        - ✅ Telangana Legislature
        - ⏳ All other states: PLANNED / NOT_IMPLEMENTED
        """)


def _display_run_result(result: dict) -> None:
    """Display a monitoring run result in a structured layout."""
    if not result:
        return

    status = result.get("status", "UNKNOWN")
    status_color = "normal"
    if status == "SUCCESS":
        status_icon = "✅"
    elif "PARTIAL" in status:
        status_icon = "⚠️"
    elif status == "FAILED":
        status_icon = "❌"
    else:
        status_icon = "ℹ️"

    cols = st.columns(6)
    cols[0].metric("Status", f"{status_icon} {status}")
    cols[1].metric("Sources Checked", result.get("sources_checked", 0))
    cols[2].metric("New Bills", result.get("new_bills", 0))
    cols[3].metric("Changes", result.get("changed_bills", 0))
    cols[4].metric("Doc Changes", result.get("document_changes", 0))
    cols[5].metric("Errors", result.get("errors", 0))

    if result.get("completed_at"):
        st.caption(f"Completed: {result['completed_at']} | Duration: {result.get('duration_seconds', 0):.1f}s")

    # Source-level results
    source_results = result.get("source_results", [])
    if source_results:
        with st.expander(f"Source Details ({len(source_results)} sources)", expanded=False):
            for sr in source_results:
                icon = "✅" if sr.get("success") else "❌"
                source_id = sr.get("source_id", "unknown")
                new_b = sr.get("new_bills", 0)
                changed_b = sr.get("changed_bills", 0)
                err = sr.get("error", "")
                dur = sr.get("duration_seconds", 0)
                label = f"{icon} **{source_id}** — {new_b} new, {changed_b} changed"
                if err:
                    label += f" | Error: {err[:60]}"
                st.markdown(label)


def _render_source_table(registry) -> None:
    """Render a table of all monitoring sources with their status."""
    try:
        import pandas as pd
        sources = registry.get_all()
        if not sources:
            st.info("No monitoring sources configured.")
            return

        rows = []
        for src in sources:
            rows.append({
                "Source ID": src.source_id,
                "Jurisdiction": src.jurisdiction.title(),
                "State": src.state or "—",
                "Source Name": src.source_name,
                "Enabled": "✅" if src.enabled else "❌",
                "Status": src.status,
                "Last Checked": src.last_checked_at or "Never",
                "Last Error": (src.last_error or "")[:40] or "—",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(
            f"Total sources: {len(sources)} | "
            f"Enabled: {sum(1 for s in sources if s.enabled)} | "
            f"Implemented states: {len(registry.get_implemented_states())}"
        )
    except Exception as e:
        st.warning(f"Could not load source table: {e}")


def _render_events_feed(feed) -> None:
    """Render the recent notification events feed."""
    try:
        events = feed.get_recent_events(limit=20)
        if not events:
            st.info("No legislative events recorded yet. Run 'Check Now' to start monitoring.")
            return

        for event in events:
            event_type = event.get("event_type", "UNKNOWN")
            bill_title = event.get("bill_title", "Unknown Bill")
            jurisdiction = event.get("jurisdiction", "")
            state = event.get("state")
            detected_at = event.get("detected_at", "")[:19]

            if event_type == "NEW_BILL":
                icon = "🆕"
            elif event_type == "STATUS_CHANGED":
                icon = "🔄"
            elif event_type == "DOCUMENT_CHANGED":
                icon = "📄"
            elif event_type == "DATE_CHANGED":
                icon = "📅"
            else:
                icon = "ℹ️"

            loc = f"[{state}]" if state else "[Central]"
            summary = event.get("summary", "")
            st.markdown(
                f"{icon} **{event_type}** {loc} — {bill_title[:60]} "
                f"<span style='color:gray; font-size:0.85em'>{detected_at}</span>",
                unsafe_allow_html=True,
            )
            if summary:
                st.caption(f"  {summary}")
    except Exception as e:
        st.warning(f"Could not load events feed: {e}")
