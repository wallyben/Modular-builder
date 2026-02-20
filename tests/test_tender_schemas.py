import pytest
from pydantic import ValidationError

from modules.tender.schemas import (
    ComplianceRow,
    Requirement,
    TenderExtraction,
    TenderMatrix,
)


def _make_requirement(**kwargs):
    defaults = dict(
        id="REQ-001",
        text="Supplier must hold ISO certification.",
        category="mandatory",
        evidence_needed=["ISO certificate"],
    )
    return Requirement(**{**defaults, **kwargs})


class TestRequirement:
    def test_valid_mandatory(self):
        r = _make_requirement()
        assert r.id == "REQ-001"
        assert r.category == "mandatory"

    def test_valid_rated(self):
        r = _make_requirement(category="rated")
        assert r.category == "rated"

    def test_valid_info(self):
        r = _make_requirement(category="info", evidence_needed=[])
        assert r.evidence_needed == []

    def test_invalid_category(self):
        with pytest.raises(ValidationError):
            _make_requirement(category="optional")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Requirement(
                id="R1",
                text="t",
                category="info",
                evidence_needed=[],
                unknown_field="x",
            )


class TestTenderExtraction:
    def test_empty_requirements_allowed(self):
        e = TenderExtraction(requirements=[])
        assert e.requirements == []

    def test_multiple_requirements(self):
        reqs = [
            _make_requirement(id="R1"),
            _make_requirement(id="R2", category="rated"),
        ]
        e = TenderExtraction(requirements=reqs)
        assert len(e.requirements) == 2

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            TenderExtraction(requirements=[], extra="nope")


class TestComplianceRow:
    def test_valid_unknown(self):
        row = ComplianceRow(requirement_id="REQ-001", status="unknown", notes="")
        assert row.status == "unknown"

    def test_all_statuses(self):
        for status in ("unknown", "met", "partial", "missing"):
            row = ComplianceRow(requirement_id="R", status=status, notes="")
            assert row.status == status

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            ComplianceRow(requirement_id="R", status="pending", notes="")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            ComplianceRow(requirement_id="R", status="met", notes="", foo="bar")


class TestTenderMatrix:
    def test_empty_rows(self):
        m = TenderMatrix(rows=[])
        assert m.rows == []

    def test_rows_preserved(self):
        rows = [
            ComplianceRow(requirement_id="R1", status="met", notes="Certified"),
            ComplianceRow(requirement_id="R2", status="missing", notes="Not provided"),
        ]
        m = TenderMatrix(rows=rows)
        assert len(m.rows) == 2
        assert m.rows[0].requirement_id == "R1"
