"""
services/monitoring/__init__.py
================================
Legislative Monitoring & Update Scheduler Package.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.

This package provides:
- MonitoringRunner   — orchestrates complete monitoring runs
- LegislativeScheduler — manages scheduled/manual execution
- CentralMonitor    — checks Central Government legislative sources
- StateMonitor      — checks State legislative sources (AP, KA, KL, TS)
- LegislativeChangeDetector — deterministic bill change detection
- UpdateProcessor   — handles new bill and changed bill processing
- LegislativeEventFeed — backend "What's New" notification event feed
- MonitoringSourceRegistry — unified source registry (Central + States)
"""

from __future__ import annotations

from services.monitoring.base_monitor import BaseMonitor, MonitorResult
from services.monitoring.change_detector import LegislativeChangeDetector
from services.monitoring.monitoring_runner import MonitoringRunner
from services.monitoring.notification_events import LegislativeEventFeed
from services.monitoring.scheduler import LegislativeScheduler
from services.monitoring.source_registry import MonitoringSourceRegistry
from services.monitoring.update_processor import UpdateProcessor

__all__ = [
    "BaseMonitor",
    "LegislativeChangeDetector",
    "LegislativeEventFeed",
    "LegislativeScheduler",
    "MonitoringRunner",
    "MonitoringSourceRegistry",
    "MonitorResult",
    "UpdateProcessor",
]
