"""
dashboard/utils/formatting.py
=============================
Display formatters, style tokens, and badge generators for the dashboard UI.
"""

from __future__ import annotations

from typing import Any, Optional

# Color mapping for risk categories
RISK_COLORS: dict[str, str] = {
    "VERY_LOW": "#10B981",   # Emerald Green
    "LOW": "#34D399",        # Light Green
    "MODERATE": "#F59E0B",   # Amber / Orange
    "HIGH": "#EF4444",       # Crimson Red
    "VERY_HIGH": "#B91C1C",  # Deep Red
    "UNKNOWN": "#6B7280",    # Neutral Gray
}

# Color mapping for predicted direction
DIRECTION_COLORS: dict[str, str] = {
    "POSITIVE": "#10B981",  # Green
    "NEGATIVE": "#EF4444",  # Red
    "NEUTRAL": "#6B7280",   # Gray
    "UNKNOWN": "#9CA3AF",
}

# Color mapping for anticipation evidence levels
ANTICIPATION_COLORS: dict[str, str] = {
    "NO_EVIDENCE": "#10B981",        # Green (low pre-event diffusion)
    "WEAK_EVIDENCE": "#3B82F6",      # Blue
    "MODERATE_EVIDENCE": "#F59E0B",  # Amber
    "STRONG_EVIDENCE": "#EF4444",    # Red (high pricing-in risk)
}


def format_number(val: Optional[float | int], decimals: int = 2) -> str:
    """Format a numeric value with given decimal precision, handling None/NaN."""
    if val is None:
        return "N/A"
    try:
        import math
        if math.isnan(val) or math.isinf(val):
            return "N/A"
        return f"{val:.{decimals}f}"
    except (TypeError, ValueError):
        return str(val)


def format_percentage(val: Optional[float], decimals: int = 1) -> str:
    """Format a fraction [0.0, 1.0] as a percentage string (e.g. 85.4%)."""
    if val is None:
        return "N/A"
    try:
        import math
        if math.isnan(val) or math.isinf(val):
            return "N/A"
        return f"{val * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"


def format_prob(val: Optional[float], decimals: int = 3) -> str:
    """Format a probability value."""
    return format_number(val, decimals=decimals)


def format_currency(val: Optional[float], prefix: str = "₹") -> str:
    """Format an amount in Crores or Lakhs."""
    if val is None:
        return "N/A"
    try:
        import math
        if math.isnan(val) or math.isinf(val):
            return "N/A"
        if abs(val) >= 10000:
            return f"{prefix}{val / 100000:.2f} Lakh Cr"
        return f"{prefix}{val:,.2f} Cr"
    except (TypeError, ValueError):
        return f"{prefix}{val}"


def format_risk_category(category: Optional[str]) -> str:
    """Format risk category with standardized casing."""
    if not category:
        return "UNKNOWN"
    return category.replace("_", " ").title()


def format_direction(direction: Optional[str]) -> str:
    """Format predicted direction string."""
    if not direction:
        return "Neutral"
    return direction.capitalize()


def get_risk_badge(category: Optional[str]) -> str:
    """Return an HTML colored badge for risk category."""
    cat = (category or "UNKNOWN").upper()
    color = RISK_COLORS.get(cat, "#6B7280")
    label = format_risk_category(cat)
    return f'<span style="background-color: {color}20; color: {color}; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85em; border: 1px solid {color}40;">{label}</span>'


def get_direction_badge(direction: Optional[str]) -> str:
    """Return an HTML colored badge for predicted direction."""
    d = (direction or "NEUTRAL").upper()
    color = DIRECTION_COLORS.get(d, "#6B7280")
    label = format_direction(d)
    icon = "▲" if d == "POSITIVE" else "▼" if d == "NEGATIVE" else "■"
    return f'<span style="background-color: {color}20; color: {color}; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85em; border: 1px solid {color}40;">{icon} {label}</span>'


def get_anticipation_badge(tier: Optional[str]) -> str:
    """Return an HTML badge for anticipation evidence tier."""
    t = (tier or "NO_EVIDENCE").upper()
    color = ANTICIPATION_COLORS.get(t, "#6B7280")
    label = t.replace("_", " ").title()
    return f'<span style="background-color: {color}20; color: {color}; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85em; border: 1px solid {color}40;">{label}</span>'
