"""
utils/state_normalizer.py
=========================
Indian State and Union Territory name normalisation.

Provides canonical names and normalises inconsistent representations
(e.g., 'karnataka', 'Karnataka State', 'KA', 'State of Karnataka') into
canonical Indian State and Union Territory names.

This module is standalone and reusable across schemas, repositories,
and validation components.
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Canonical Indian States (28) & Union Territories (8)
# ---------------------------------------------------------------------------

CANONICAL_INDIAN_STATES: tuple[str, ...] = (
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
)

CANONICAL_UNION_TERRITORIES: tuple[str, ...] = (
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
)

ALL_CANONICAL_REGIONS: tuple[str, ...] = (
    CANONICAL_INDIAN_STATES + CANONICAL_UNION_TERRITORIES
)

_CANONICAL_SET: frozenset[str] = frozenset(ALL_CANONICAL_REGIONS)

# ---------------------------------------------------------------------------
# Aliases & abbreviations mapped to canonical names (case-folded keys)
# ---------------------------------------------------------------------------

_STATE_ALIASES: dict[str, str] = {
    # Andhra Pradesh
    "ap": "Andhra Pradesh",
    "andhra": "Andhra Pradesh",
    "andhra pradesh": "Andhra Pradesh",
    "amaravati": "Andhra Pradesh",
    # Arunachal Pradesh
    "ar": "Arunachal Pradesh",
    "arunachal": "Arunachal Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "itanagar": "Arunachal Pradesh",
    # Assam
    "as": "Assam",
    "assam": "Assam",
    "asom": "Assam",
    "guwahati": "Assam",
    "dispur": "Assam",
    # Bihar
    "br": "Bihar",
    "bihar": "Bihar",
    "patna": "Bihar",
    # Chhattisgarh
    "cg": "Chhattisgarh",
    "chhattisgarh": "Chhattisgarh",
    "chhatisgarh": "Chhattisgarh",
    "raipur": "Chhattisgarh",
    # Goa
    "ga": "Goa",
    "goa": "Goa",
    "panaji": "Goa",
    # Gujarat
    "gj": "Gujarat",
    "guj": "Gujarat",
    "gujarat": "Gujarat",
    "ahmedabad": "Gujarat",
    "gandhinagar": "Gujarat",
    # Haryana
    "hr": "Haryana",
    "haryana": "Haryana",
    "gurgaon": "Haryana",
    "gurugram": "Haryana",
    # Himachal Pradesh
    "hp": "Himachal Pradesh",
    "himachal": "Himachal Pradesh",
    "himachal pradesh": "Himachal Pradesh",
    "shimla": "Himachal Pradesh",
    # Jharkhand
    "jh": "Jharkhand",
    "jharkhand": "Jharkhand",
    "ranchi": "Jharkhand",
    # Karnataka
    "ka": "Karnataka",
    "kar": "Karnataka",
    "karnataka": "Karnataka",
    "bangalore": "Karnataka",
    "bengaluru": "Karnataka",
    # Kerala
    "kl": "Kerala",
    "kerala": "Kerala",
    "trivandrum": "Kerala",
    "thiruvananthapuram": "Kerala",
    "cochin": "Kerala",
    "kochi": "Kerala",
    # Madhya Pradesh
    "mp": "Madhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "bhopal": "Madhya Pradesh",
    "indore": "Madhya Pradesh",
    # Maharashtra
    "mh": "Maharashtra",
    "mah": "Maharashtra",
    "maharashtra": "Maharashtra",
    "mumbai": "Maharashtra",
    "bombay": "Maharashtra",
    "pune": "Maharashtra",
    # Manipur
    "mn": "Manipur",
    "manipur": "Manipur",
    "imphal": "Manipur",
    # Meghalaya
    "ml": "Meghalaya",
    "meghalaya": "Meghalaya",
    "shillong": "Meghalaya",
    # Mizoram
    "mz": "Mizoram",
    "mizoram": "Mizoram",
    "aizawl": "Mizoram",
    # Nagaland
    "nl": "Nagaland",
    "nagaland": "Nagaland",
    "kohima": "Nagaland",
    # Odisha
    "od": "Odisha",
    "or": "Odisha",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "bhubaneswar": "Odisha",
    # Punjab
    "pb": "Punjab",
    "punjab": "Punjab",
    # Rajasthan
    "rj": "Rajasthan",
    "raj": "Rajasthan",
    "rajasthan": "Rajasthan",
    "jaipur": "Rajasthan",
    # Sikkim
    "sk": "Sikkim",
    "sikkim": "Sikkim",
    "gangtok": "Sikkim",
    # Tamil Nadu
    "tn": "Tamil Nadu",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "chennai": "Tamil Nadu",
    "madras": "Tamil Nadu",
    # Telangana
    "ts": "Telangana",
    "telangana": "Telangana",
    "hyderabad": "Telangana",
    # Tripura
    "tr": "Tripura",
    "tripura": "Tripura",
    "agartala": "Tripura",
    # Uttar Pradesh
    "up": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "uttarpradesh": "Uttar Pradesh",
    "lucknow": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "noida": "Uttar Pradesh",
    # Uttarakhand
    "uk": "Uttarakhand",
    "ut": "Uttarakhand",
    "ua": "Uttarakhand",
    "uttarakhand": "Uttarakhand",
    "uttaranchal": "Uttarakhand",
    "dehradun": "Uttarakhand",
    # West Bengal
    "wb": "West Bengal",
    "west bengal": "West Bengal",
    "westbengal": "West Bengal",
    "kolkata": "West Bengal",
    "calcutta": "West Bengal",
    # Union Territories
    # Andaman and Nicobar Islands
    "an": "Andaman and Nicobar Islands",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "andaman & nicobar": "Andaman and Nicobar Islands",
    "andaman & nicobar islands": "Andaman and Nicobar Islands",
    "port blair": "Andaman and Nicobar Islands",
    # Chandigarh
    "ch": "Chandigarh",
    "chandigarh": "Chandigarh",
    # Dadra and Nagar Haveli and Daman and Diu
    "dd": "Dadra and Nagar Haveli and Daman and Diu",
    "dnh": "Dadra and Nagar Haveli and Daman and Diu",
    "dnhdd": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli and daman and diu": (
        "Dadra and Nagar Haveli and Daman and Diu"
    ),
    "dadra & nagar haveli and daman & diu": (
        "Dadra and Nagar Haveli and Daman and Diu"
    ),
    # Delhi
    "dl": "Delhi",
    "del": "Delhi",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "nct of delhi": "Delhi",
    "nct delhi": "Delhi",
    "national capital territory of delhi": "Delhi",
    # Jammu and Kashmir
    "jk": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "j and k": "Jammu and Kashmir",
    "jammu & kashmir": "Jammu and Kashmir",
    "jammu and kashmir": "Jammu and Kashmir",
    "srinagar": "Jammu and Kashmir",
    "jammu": "Jammu and Kashmir",
    # Ladakh
    "la": "Ladakh",
    "ladakh": "Ladakh",
    "leh": "Ladakh",
    # Lakshadweep
    "ld": "Lakshadweep",
    "lakshadweep": "Lakshadweep",
    "kavaratti": "Lakshadweep",
    # Puducherry
    "py": "Puducherry",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
}

# Precompile regexes for stripping affixes
_PREFIX_PATTERN = re.compile(
    r"^(?:the\s+)?(?:state\s+of\s+|government\s+of\s+|govt\s+of\s+|ut\s+of\s+|union\s+territory\s+of\s+)",
    re.IGNORECASE,
)
_SUFFIX_PATTERN = re.compile(
    r"\s+(?:state|ut|union\s+territory|government|govt)$",
    re.IGNORECASE,
)


def normalize_state(name: Optional[str]) -> Optional[str]:
    """
    Normalise an Indian State or Union Territory name into canonical form.

    Parameters
    ----------
    name : str | None
        Input state name, alias, abbreviation, or representation with affixes
        (e.g., 'Karnataka', 'karnataka', 'Karnataka State', 'KA', 'State of Karnataka').

    Returns
    -------
    str | None
        Canonical Indian State or UT name, or None if input is empty/None.
        If the name cannot be mapped to a known state, the cleaned stripped
        input is returned in Title Case.

    Examples
    --------
    >>> normalize_state("Karnataka")
    'Karnataka'
    >>> normalize_state("karnataka")
    'Karnataka'
    >>> normalize_state("Karnataka State")
    'Karnataka'
    >>> normalize_state("State of Maharashtra")
    'Maharashtra'
    >>> normalize_state("KA")
    'Karnataka'
    >>> normalize_state(None)
    None
    """
    if name is None:
        return None

    cleaned = name.strip()
    if not cleaned:
        return None

    # Check direct canonical match
    if cleaned in _CANONICAL_SET:
        return cleaned

    # Strip prefixes and suffixes
    stripped = _PREFIX_PATTERN.sub("", cleaned).strip()
    stripped = _SUFFIX_PATTERN.sub("", stripped).strip()

    # Case-folded lookup
    key = stripped.lower()
    if key in _STATE_ALIASES:
        return _STATE_ALIASES[key]

    # Also check unstripped lowercase key
    raw_key = cleaned.lower()
    if raw_key in _STATE_ALIASES:
        return _STATE_ALIASES[raw_key]

    # Fallback to title-cased stripped text if matches canonical set
    title_cased = stripped.title()
    if title_cased in _CANONICAL_SET:
        return title_cased

    return title_cased


def is_valid_state(name: str) -> bool:
    """
    Return True if the name corresponds to a recognised Indian State or UT.

    Parameters
    ----------
    name : str
        State or UT name to check.

    Returns
    -------
    bool
    """
    normalized = normalize_state(name)
    return normalized in _CANONICAL_SET if normalized else False


def get_canonical_states() -> list[str]:
    """Return a sorted list of all 28 canonical Indian States."""
    return sorted(CANONICAL_INDIAN_STATES)


def get_canonical_uts() -> list[str]:
    """Return a sorted list of all 8 canonical Indian Union Territories."""
    return sorted(CANONICAL_UNION_TERRITORIES)


def get_all_states_and_uts() -> list[str]:
    """Return a sorted list of all 36 canonical Indian States and Union Territories."""
    return sorted(ALL_CANONICAL_REGIONS)
