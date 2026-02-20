import pytest

from modules.tender.schemas import (
    ComplianceRow,
    Requirement,
    TenderExtraction,
    TenderMatrix,
)
from modules.tender.scoring import identify_evidence_gaps, score_matrix


def _matrix(*statuses) -> TenderMatrix:
    rows = [
        ComplianceRow(requirement_id=f"R{i}", status=s, notes="")
        for i, s in enumerate(statuses, 1)
    ]
    return TenderMatrix(rows=rows)


def _extraction_with_evidence(req_id: str, status: str, evidence: list) -> tuple:
    req = Requirement(id=req_id, text="t", category="mandatory", evidence_needed=evidence)
    extraction = TenderExtraction(requirements=[req])
    matrix = TenderMatrix(
        rows=[ComplianceRow(requirement_id=req_id, status=status, notes="")]
    )
    return extraction, matrix


class TestScoreMatrix:
    def test_all_met(self):
        s = score_matrix(_matrix("met", "met", "met"))
        assert s.total == 3
        assert s.met == 3
        assert s.score == 1.0

    def test_all_missing(self):
        s = score_matrix(_matrix("missing", "missing"))
        assert s.score == 0.0
        assert s.missing == 2
        assert s.missing_ids == ["R1", "R2"]

    def test_all_partial(self):
        s = score_matrix(_matrix("partial", "partial"))
        assert s.score == pytest.approx(0.5)
        assert s.partial == 2

    def test_mixed(self):
        # 1 met, 1 partial, 1 missing, 1 unknown → (1 + 0.5) / 4 = 0.375
        s = score_matrix(_matrix("met", "partial", "missing", "unknown"))
        assert s.total == 4
        assert s.met == 1
        assert s.partial == 1
        assert s.missing == 1
        assert s.score == pytest.approx(0.375)

    def test_zero_total(self):
        s = score_matrix(TenderMatrix(rows=[]))
        assert s.total == 0
        assert s.score == 0.0

    def test_missing_ids_only_missing_status(self):
        s = score_matrix(_matrix("met", "missing", "partial", "missing"))
        assert s.missing_ids == ["R2", "R4"]

    def test_unknown_not_counted_in_met_partial_missing(self):
        s = score_matrix(_matrix("unknown", "unknown"))
        assert s.met == 0
        assert s.partial == 0
        assert s.missing == 0
        assert s.score == 0.0


class TestIdentifyEvidenceGaps:
    def test_missing_with_evidence(self):
        extraction, matrix = _extraction_with_evidence("R1", "missing", ["cert.pdf"])
        gaps = identify_evidence_gaps(extraction, matrix)
        assert len(gaps) == 1
        assert gaps[0].requirement_id == "R1"
        assert gaps[0].missing_evidence == ["cert.pdf"]

    def test_partial_with_evidence(self):
        extraction, matrix = _extraction_with_evidence("R1", "partial", ["ref.doc"])
        gaps = identify_evidence_gaps(extraction, matrix)
        assert len(gaps) == 1

    def test_met_excluded(self):
        extraction, matrix = _extraction_with_evidence("R1", "met", ["cert.pdf"])
        gaps = identify_evidence_gaps(extraction, matrix)
        assert gaps == []

    def test_unknown_excluded(self):
        extraction, matrix = _extraction_with_evidence("R1", "unknown", ["cert.pdf"])
        gaps = identify_evidence_gaps(extraction, matrix)
        assert gaps == []

    def test_missing_no_evidence_excluded(self):
        extraction, matrix = _extraction_with_evidence("R1", "missing", [])
        gaps = identify_evidence_gaps(extraction, matrix)
        assert gaps == []

    def test_multiple_requirements(self):
        reqs = [
            Requirement(id="R1", text="t", category="mandatory", evidence_needed=["a"]),
            Requirement(id="R2", text="t", category="mandatory", evidence_needed=["b"]),
            Requirement(id="R3", text="t", category="mandatory", evidence_needed=["c"]),
        ]
        extraction = TenderExtraction(requirements=reqs)
        matrix = TenderMatrix(rows=[
            ComplianceRow(requirement_id="R1", status="missing", notes=""),
            ComplianceRow(requirement_id="R2", status="met", notes=""),
            ComplianceRow(requirement_id="R3", status="partial", notes=""),
        ])
        gaps = identify_evidence_gaps(extraction, matrix)
        assert len(gaps) == 2
        ids = {g.requirement_id for g in gaps}
        assert ids == {"R1", "R3"}
