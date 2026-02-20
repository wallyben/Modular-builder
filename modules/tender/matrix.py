from __future__ import annotations

from modules.tender.schemas import ComplianceRow, TenderExtraction, TenderMatrix


def build_compliance_matrix(extraction: TenderExtraction) -> TenderMatrix:
    """Build a compliance matrix from an extraction result.

    All rows default to status='unknown' and notes='' pending review.
    """
    rows = [
        ComplianceRow(
            requirement_id=req.id,
            status="unknown",
            notes="",
        )
        for req in extraction.requirements
    ]
    return TenderMatrix(rows=rows)
