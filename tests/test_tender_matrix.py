from pathlib import Path

import pytest

from modules.tender.extract import extract_requirements_from_text
from modules.tender.matrix import build_compliance_matrix
from modules.tender.schemas import Requirement, TenderExtraction, TenderMatrix

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _extraction_with(n: int) -> TenderExtraction:
    return TenderExtraction(
        requirements=[
            Requirement(
                id=f"REQ-{i:03d}",
                text=f"Requirement {i}",
                category="mandatory",
                evidence_needed=[],
            )
            for i in range(1, n + 1)
        ]
    )


class TestBuildComplianceMatrix:
    def test_returns_tender_matrix(self):
        extraction = _extraction_with(1)
        result = build_compliance_matrix(extraction)
        assert isinstance(result, TenderMatrix)

    def test_one_row_per_requirement(self):
        extraction = _extraction_with(3)
        matrix = build_compliance_matrix(extraction)
        assert len(matrix.rows) == 3

    def test_row_ids_match_requirements(self):
        extraction = _extraction_with(2)
        matrix = build_compliance_matrix(extraction)
        assert matrix.rows[0].requirement_id == "REQ-001"
        assert matrix.rows[1].requirement_id == "REQ-002"

    def test_default_status_unknown(self):
        extraction = _extraction_with(2)
        matrix = build_compliance_matrix(extraction)
        for row in matrix.rows:
            assert row.status == "unknown"

    def test_default_notes_empty(self):
        extraction = _extraction_with(2)
        matrix = build_compliance_matrix(extraction)
        for row in matrix.rows:
            assert row.notes == ""

    def test_empty_extraction(self):
        extraction = TenderExtraction(requirements=[])
        matrix = build_compliance_matrix(extraction)
        assert matrix.rows == []


class TestExtractFallback:
    def test_no_adapter_returns_extraction(self):
        result = extract_requirements_from_text("some text", adapter=None)
        assert isinstance(result, TenderExtraction)
        assert len(result.requirements) >= 1

    def test_no_adapter_requirement_is_info(self):
        result = extract_requirements_from_text("any", adapter=None)
        assert all(r.category == "info" for r in result.requirements)

    def test_adapter_called_with_text(self):
        called_with = []

        def fake_adapter(text):
            called_with.append(text)
            return TenderExtraction(
                requirements=[
                    Requirement(
                        id="R1",
                        text="Comply with X.",
                        category="mandatory",
                        evidence_needed=["doc"],
                    )
                ]
            )

        result = extract_requirements_from_text("hello tender", adapter=fake_adapter)
        assert called_with == ["hello tender"]
        assert len(result.requirements) == 1
        assert result.requirements[0].id == "R1"

    def test_adapter_returning_dict(self):
        def dict_adapter(text):
            return {
                "requirements": [
                    {
                        "id": "D1",
                        "text": "Dict requirement",
                        "category": "rated",
                        "evidence_needed": [],
                    }
                ]
            }

        result = extract_requirements_from_text("text", adapter=dict_adapter)
        assert result.requirements[0].id == "D1"


class TestFixturePipeline:
    def test_fixture_file_exists(self):
        fixture = FIXTURE_DIR / "tender_text_01.txt"
        assert fixture.exists(), "Fixture file missing"

    def test_full_pipeline_with_fixture(self):
        text = (FIXTURE_DIR / "tender_text_01.txt").read_text(encoding="utf-8")
        extraction = extract_requirements_from_text(text, adapter=None)
        matrix = build_compliance_matrix(extraction)
        assert isinstance(matrix, TenderMatrix)
        assert len(matrix.rows) >= 1
        for row in matrix.rows:
            assert row.status == "unknown"
