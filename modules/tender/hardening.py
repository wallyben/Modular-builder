from __future__ import annotations

import re
from typing import TypedDict

from modules.tender.schemas import DisqualifyFlag, EvidenceMapItem

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class RequirementItem(TypedDict):
    id: str
    text: str
    level: str  # "mandatory" | "rated" | "info"


# TenderExtraction: list of RequirementItems
TenderExtraction = list[RequirementItem]

class MatrixRow(TypedDict):
    requirement_id: str
    status: str  # "met" | "partial" | "not_met" | ""


# TenderMatrix: list of MatrixRows
TenderMatrix = list[MatrixRow]


# ---------------------------------------------------------------------------
# 1) Mandatory vs Rated Separation
# ---------------------------------------------------------------------------

_MANDATORY_PATTERN = re.compile(
    r"\b(must|shall|mandatory|required|require)\b", re.IGNORECASE
)
_RATED_PATTERN = re.compile(
    r"\b(should|may|desirable|preferred|rated|scored)\b", re.IGNORECASE
)


def classify_requirement_levels(extraction: TenderExtraction) -> dict:
    """Classify each requirement as mandatory, rated, or info.

    Returns:
        {
            "mandatory_ids": list[str],
            "rated_ids": list[str],
            "info_ids": list[str],
        }
    """
    mandatory_ids: list[str] = []
    rated_ids: list[str] = []
    info_ids: list[str] = []

    for req in extraction:
        req_id = req["id"]
        text = req["text"]
        if _MANDATORY_PATTERN.search(text):
            mandatory_ids.append(req_id)
        elif _RATED_PATTERN.search(text):
            rated_ids.append(req_id)
        else:
            info_ids.append(req_id)

    return {
        "mandatory_ids": mandatory_ids,
        "rated_ids": rated_ids,
        "info_ids": info_ids,
    }


# ---------------------------------------------------------------------------
# 2) Mandatory Gap Detector
# ---------------------------------------------------------------------------

def detect_mandatory_gaps(matrix: TenderMatrix, mandatory_ids: list[str]) -> list[str]:
    """Return requirement_ids from mandatory_ids where status != 'met'."""
    mandatory_set = set(mandatory_ids)
    return [
        row["requirement_id"]
        for row in matrix
        if row["requirement_id"] in mandatory_set and row["status"] != "met"
    ]


# ---------------------------------------------------------------------------
# 3) Risk Language Detector
# ---------------------------------------------------------------------------

GENERIC_PHRASES = [
    "best in class",
    "industry-leading",
    "world class",
    "cutting edge",
    "state of the art",
    "innovative solutions",
    "leading provider",
]


def detect_generic_language(text: str) -> list[str]:
    """Return phrases from GENERIC_PHRASES found in text (case-insensitive)."""
    lower = text.lower()
    return [phrase for phrase in GENERIC_PHRASES if phrase in lower]


# ---------------------------------------------------------------------------
# 4) Coverage Split Scoring
# ---------------------------------------------------------------------------

_STATUS_SCORE = {"met": 1.0, "partial": 0.5}


def calculate_split_scores(matrix: TenderMatrix, classification: dict) -> dict:
    """Return separate compliance scores for mandatory and rated requirements.

    Score calculation: met=1, partial=0.5, anything else=0.

    Returns:
        {
            "mandatory_score": float,  # 0.0 – 1.0
            "rated_score": float,      # 0.0 – 1.0
        }
    """
    mandatory_set = set(classification.get("mandatory_ids", []))
    rated_set = set(classification.get("rated_ids", []))

    def _score(id_set: set) -> float:
        rows = [row for row in matrix if row["requirement_id"] in id_set]
        if not rows:
            return 0.0
        total = sum(_STATUS_SCORE.get(row["status"], 0.0) for row in rows)
        return round(total / len(rows), 4)

    return {
        "mandatory_score": _score(mandatory_set),
        "rated_score": _score(rated_set),
    }


# ---------------------------------------------------------------------------
# 5) Evidence Mapping
# ---------------------------------------------------------------------------

# Each entry: (pattern, evidence_terms, suggested_artifacts)
_ARTIFACT_RULES: list[tuple[re.Pattern, list[str], list[str]]] = [
    (
        re.compile(r"\binsurance\b", re.IGNORECASE),
        ["insurance"],
        ["Insurance Certificate (PDF)"],
    ),
    (
        re.compile(r"\btax\b|\brevenue\b", re.IGNORECASE),
        ["tax clearance"],
        ["Tax Clearance / Revenue Statement"],
    ),
    (
        re.compile(r"\bpolicy\b", re.IGNORECASE),
        ["policy"],
        ["Relevant Policy Document (DOCX/PDF)"],
    ),
    (
        re.compile(r"\bcvs?\b|\bexperience\b", re.IGNORECASE),
        ["cv", "experience"],
        ["Staff CVs", "Case Studies"],
    ),
    (
        re.compile(r"\bmethod\s+statement\b", re.IGNORECASE),
        ["method statement"],
        ["Method Statement"],
    ),
    (
        re.compile(r"\brisk\s+assessment\b|\brams\b", re.IGNORECASE),
        ["risk assessment"],
        ["Risk Assessment"],
    ),
]


def build_evidence_map(extraction: TenderExtraction) -> list[EvidenceMapItem]:
    """For each requirement derive evidence_needed and suggested_artifacts from text keywords."""
    items: list[EvidenceMapItem] = []
    for req in extraction:
        text = req["text"]
        evidence_needed: list[str] = []
        suggested_artifacts: list[str] = []

        for pattern, ev_terms, artifacts in _ARTIFACT_RULES:
            if pattern.search(text):
                for term in ev_terms:
                    if term not in evidence_needed:
                        evidence_needed.append(term)
                for art in artifacts:
                    if art not in suggested_artifacts:
                        suggested_artifacts.append(art)

        if not suggested_artifacts:
            suggested_artifacts = ["Supporting Document"]

        items.append(
            EvidenceMapItem(
                requirement_id=req["id"],
                evidence_needed=evidence_needed,
                suggested_artifacts=suggested_artifacts,
            )
        )
    return items


# ---------------------------------------------------------------------------
# 6) Disqualification Risk Flags
# ---------------------------------------------------------------------------

# Each entry: (pattern, code, message)
_DISQUALIFY_RULES: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"\binsurance\b", re.IGNORECASE),
        "insurance",
        "Insurance requirement detected — certificate must be current and adequate.",
    ),
    (
        re.compile(r"\btax\s+clearance\b|\brevenue\b", re.IGNORECASE),
        "tax_clearance",
        "Tax clearance requirement detected — certificate must be current.",
    ),
    (
        re.compile(r"\bsafety\s+statement\b|\brams\b|\brisk\s+assessment\b", re.IGNORECASE),
        "health_safety",
        "Health & safety requirement detected — RAMS / safety statement required.",
    ),
    (
        re.compile(r"\baudited\s+accounts\b|\bturnover\b", re.IGNORECASE),
        "financials",
        "Financial requirement detected — audited accounts or turnover threshold applies.",
    ),
    (
        re.compile(
            r"\bminimum\b.{0,50}\byears\b|\byears\b.{0,50}\bexperience\b"
            r"|\bminimum\b.{0,50}\bexperience\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "experience",
        "Experience requirement detected — minimum years / experience threshold applies.",
    ),
]


def detect_disqualify_flags(extraction: TenderExtraction) -> list[DisqualifyFlag]:
    """Return a DisqualifyFlag for each requirement that matches a disqualification pattern."""
    flags: list[DisqualifyFlag] = []
    for req in extraction:
        text = req["text"]
        req_id = req["id"]
        for pattern, code, message in _DISQUALIFY_RULES:
            if pattern.search(text):
                flags.append(
                    DisqualifyFlag(code=code, requirement_id=req_id, message=message)  # type: ignore[arg-type]
                )
    return flags
