from __future__ import annotations

from modules.tender.schemas import (
    CoverageSummary,
    EvidenceGap,
    TenderExtraction,
    TenderMatrix,
)


def score_matrix(matrix: TenderMatrix) -> CoverageSummary:
    total = len(matrix.rows)
    met = sum(1 for r in matrix.rows if r.status == "met")
    partial = sum(1 for r in matrix.rows if r.status == "partial")
    missing = sum(1 for r in matrix.rows if r.status == "missing")
    score = (met + 0.5 * partial) / total if total > 0 else 0.0
    missing_ids = [r.requirement_id for r in matrix.rows if r.status == "missing"]
    return CoverageSummary(
        total=total,
        met=met,
        partial=partial,
        missing=missing,
        score=score,
        missing_ids=missing_ids,
    )


def identify_evidence_gaps(
    extraction: TenderExtraction,
    matrix: TenderMatrix,
) -> list[EvidenceGap]:
    gap_statuses = {"missing", "partial"}
    row_status = {r.requirement_id: r.status for r in matrix.rows}
    gaps = []
    for req in extraction.requirements:
        if row_status.get(req.id) in gap_statuses and req.evidence_needed:
            gaps.append(
                EvidenceGap(
                    requirement_id=req.id,
                    missing_evidence=req.evidence_needed,
                )
            )
    return gaps
