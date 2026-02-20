from __future__ import annotations

from .schemas import AwardNotice, Prospect

# Keyword groups with weights (all lowercased)
_FM_KEYWORDS: list[tuple[list[str], int, str]] = [
    (["facilities management", "facilities services", "fm services"], 30, "Core FM contract"),
    (["cleaning", "janitorial", "housekeeping"], 20, "Cleaning/janitorial scope"),
    (["maintenance", "planned maintenance", "reactive maintenance"], 15, "Maintenance scope"),
    (["grounds", "grounds maintenance", "landscaping", "horticulture"], 15, "Grounds maintenance scope"),
    (["m&e", "mechanical", "electrical", "hvac", "building services"], 15, "M&E/HVAC scope"),
    (["waste management", "waste collection", "recycling"], 10, "Waste management scope"),
    (["security", "access control", "manned guarding"], 10, "Security services scope"),
    (["catering", "hospitality", "vending"], 10, "Catering scope"),
    (["pest control"], 5, "Pest control scope"),
    (["total facilities", "integrated facilities", "tfm"], 20, "Total/integrated FM"),
]


def score_prospect(award: AwardNotice) -> Prospect:
    haystack = " ".join(
        filter(None, [award.title, award.description])
    ).lower()

    total = 0
    rationale: list[str] = []

    for keywords, weight, label in _FM_KEYWORDS:
        for kw in keywords:
            if kw in haystack:
                total += weight
                rationale.append(f"{label} (+{weight}): matched '{kw}'")
                break  # only score each group once

    score = min(total, 100)

    company_name = award.winner_name or "Unknown Company"

    return Prospect(
        company_name=company_name,
        niche="facilities_management",
        authority=award.authority,
        contract_title=award.title,
        award_date=award.award_date,
        value_eur=award.value_eur,
        score=score,
        rationale=rationale if rationale else ["No FM keywords matched"],
    )
