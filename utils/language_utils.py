"""
utils/language_utils.py
=======================
Deterministic language and Indic script detection utilities.

Analyzes text character-by-character against Unicode block definitions
to identify primary languages, multilingual content, and script distributions
without external heavyweight ML/NLP dependencies.
"""

from __future__ import annotations

import unicodedata
from typing import Any


SCRIPT_RANGES: dict[str, tuple[int, int]] = {
    "Malayalam": (0x0D00, 0x0D7F),
    "Telugu": (0x0C00, 0x0C7F),
    "Kannada": (0x0C80, 0x0CFF),
    "Devanagari": (0x0900, 0x097F),
    "Tamil": (0x0B80, 0x0BFF),
    "Bengali": (0x0980, 0x09FF),
    "Gujarati": (0x0A80, 0x0AFF),
    "Gurmukhi": (0x0A00, 0x0A7F),
    "Odia": (0x0B00, 0x0B7F),
    "Arabic/Urdu": (0x0600, 0x06FF),
}


def detect_script(text: str) -> dict[str, float]:
    """
    Compute relative frequency of Unicode scripts in the given text.

    Parameters
    ----------
    text : str
        Input string.

    Returns
    -------
    dict[str, float]
        Mapping from script name to percentage of alphabetic characters (0.0 to 100.0).
    """
    if not text or not isinstance(text, str):
        return {"English": 100.0}

    counts: dict[str, int] = {
        "Latin/English": 0,
        "Malayalam": 0,
        "Telugu": 0,
        "Kannada": 0,
        "Devanagari": 0,
        "Tamil": 0,
        "Arabic/Urdu": 0,
        "Other": 0,
    }

    total_letters = 0

    for ch in text:
        cat = unicodedata.category(ch)
        # Only evaluate letters/marks
        if not (cat.startswith("L") or cat.startswith("M")):
            continue

        total_letters += 1
        cp = ord(ch)

        matched = False
        for script, (low, high) in SCRIPT_RANGES.items():
            if low <= cp <= high:
                if script in counts:
                    counts[script] += 1
                else:
                    counts["Other"] += 1
                matched = True
                break

        if not matched:
            if (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A) or (0x00C0 <= cp <= 0x024F):
                counts["Latin/English"] += 1
            else:
                counts["Other"] += 1

    if total_letters == 0:
        return {"English": 100.0}

    return {
        script: round((count / total_letters) * 100.0, 2)
        for script, count in counts.items()
        if count > 0
    }


def detect_language(text: str, default_state: str = "") -> dict[str, Any]:
    """
    Detect primary language, secondary language, and multilingual status of text.

    Parameters
    ----------
    text : str
        Corpus or metadata string.
    default_state : str
        State context for disambiguation.

    Returns
    -------
    dict[str, Any]
        Dictionary with:
        - primary_language: str (e.g. "English", "Malayalam", "Telugu", "Kannada")
        - is_multilingual: bool
        - languages_detected: list[str]
        - script_breakdown: dict[str, float]
    """
    scripts = detect_script(text)

    # Convert Latin/English key
    latin_pct = scripts.get("Latin/English", 0.0)
    malayalam_pct = scripts.get("Malayalam", 0.0)
    telugu_pct = scripts.get("Telugu", 0.0)
    kannada_pct = scripts.get("Kannada", 0.0)
    devanagari_pct = scripts.get("Devanagari", 0.0)
    tamil_pct = scripts.get("Tamil", 0.0)
    urdu_pct = scripts.get("Arabic/Urdu", 0.0)

    indic_scripts = [
        ("Malayalam", malayalam_pct),
        ("Telugu", telugu_pct),
        ("Kannada", kannada_pct),
        ("Hindi", devanagari_pct),
        ("Tamil", tamil_pct),
        ("Urdu", urdu_pct),
    ]

    indic_scripts.sort(key=lambda x: x[1], reverse=True)
    top_indic_name, top_indic_pct = indic_scripts[0]

    languages: list[str] = []
    if latin_pct > 5.0:
        languages.append("English")
    for name, pct in indic_scripts:
        if pct >= 1.0:
            languages.append(name)

    if not languages:
        languages = ["English"]

    # Determine primary language
    if top_indic_pct > 50.0:
        primary = top_indic_name
    elif top_indic_pct >= 1.0 and latin_pct >= 10.0:
        primary = f"Bilingual (English / {top_indic_name})"
    elif latin_pct >= 50.0:
        primary = "English"
    elif top_indic_pct > 0.0:
        primary = top_indic_name
    else:
        primary = "English"

    is_multilingual = len(languages) > 1

    return {
        "primary_language": primary,
        "is_multilingual": is_multilingual,
        "languages_detected": languages,
        "script_breakdown": scripts,
    }
