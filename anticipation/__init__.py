"""
anticipation package
====================
Anticipation Bias / Pre-Event Information Analysis Engine for Task 6.5.

Investigates pre-event legislative market anticipation, abnormal return drift,
and pre-T0 information signals with strict anti-leakage guarantees.
"""

from anticipation.market_analyzer import PreEventMarketAnalyzer, parse_window_offsets
from anticipation.signal_detector import PreEventSignalDetector
from anticipation.scorer import AnticipationScorer
from anticipation.engine import AnticipationBiasEngine

__all__ = [
    "PreEventMarketAnalyzer",
    "parse_window_offsets",
    "PreEventSignalDetector",
    "AnticipationScorer",
    "AnticipationBiasEngine",
]
