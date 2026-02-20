from __future__ import annotations

import re

from .schemas import AwardNotice

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}"
    r"|\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May"
    r"|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?"
    r"|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}"
    r"|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)

_VALUE_RE = re.compile(
    r"(?:EUR|€|euro)\s*([0-9][0-9,\.]*[kKmMbB]?)"
    r"|([0-9][0-9,\.]*[kKmMbB]?)\s*(?:EUR|€|euro)",
    re.IGNORECASE,
)

_AUTHORITY_PATTERNS = [
    re.compile(r"(?:contracting authority|awarding authority|authority)[:\s]+([^\n\r,\.]{3,80})", re.IGNORECASE),
    re.compile(r"(?:council|council of|county|department of|office of)[^\n\r,\.]{0,60}", re.IGNORECASE),
]

_TITLE_PATTERNS = [
    re.compile(r"(?:contract title|title|tender title|subject)[:\s]+([^\n\r]{5,120})", re.IGNORECASE),
    re.compile(r"(?:provision of|supply of|delivery of)\s+[^\n\r]{5,100}", re.IGNORECASE),
]

_WINNER_PATTERNS = [
    re.compile(r"(?:awarded to|contractor|supplier|winner|successful tenderer)[:\s]+([^\n\r,\.]{3,80})", re.IGNORECASE),
]

_DESC_PATTERN = re.compile(
    r"(?:description|scope|object of the contract)[:\s]+([^\n\r]{10,300})", re.IGNORECASE
)


def _parse_value(raw: str) -> float | None:
    raw = raw.replace(",", "").strip()
    multiplier = 1.0
    if raw and raw[-1].lower() == "k":
        multiplier = 1_000.0
        raw = raw[:-1]
    elif raw and raw[-1].lower() == "m":
        multiplier = 1_000_000.0
        raw = raw[:-1]
    elif raw and raw[-1].lower() == "b":
        multiplier = 1_000_000_000.0
        raw = raw[:-1]
    try:
        return float(raw) * multiplier
    except ValueError:
        return None


def _first_match(patterns: list[re.Pattern], text: str) -> str | None:
    for pat in patterns:
        m = pat.search(text)
        if m:
            groups = [g for g in m.groups() if g]
            return groups[0].strip() if groups else m.group(0).strip()
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_award_notice(text: str) -> AwardNotice:
    """Parse award notice text into an AwardNotice using regex heuristics."""
    authority = _first_match(_AUTHORITY_PATTERNS, text)
    title = _first_match(_TITLE_PATTERNS, text)
    winner_name = _first_match(_WINNER_PATTERNS, text)

    desc_m = _DESC_PATTERN.search(text)
    description = desc_m.group(1).strip() if desc_m else None

    date_m = _DATE_RE.search(text)
    award_date = date_m.group(0) if date_m else None

    value_eur: float | None = None
    val_m = _VALUE_RE.search(text)
    if val_m:
        raw = (val_m.group(1) or val_m.group(2) or "").strip()
        value_eur = _parse_value(raw)

    return AwardNotice(
        source="manual-paste",
        authority=authority,
        title=title,
        description=description,
        award_date=award_date,
        value_eur=value_eur,
        winner_name=winner_name,
    )
