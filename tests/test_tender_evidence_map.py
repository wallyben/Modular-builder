"""Tests for build_evidence_map in modules/tender/hardening.py"""
from __future__ import annotations

import pytest

from modules.tender.hardening import TenderExtraction, build_evidence_map
from modules.tender.schemas import EvidenceMapItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extraction(*texts: str) -> TenderExtraction:
    return [{"id": str(i + 1), "text": t, "level": ""} for i, t in enumerate(texts)]


def _artifacts_for(text: str) -> list[str]:
    items = build_evidence_map(_extraction(text))
    return items[0].suggested_artifacts


def _evidence_for(text: str) -> list[str]:
    items = build_evidence_map(_extraction(text))
    return items[0].evidence_needed


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

class TestReturnType:
    def test_returns_list_of_evidence_map_items(self):
        result = build_evidence_map(_extraction("Some requirement."))
        assert isinstance(result, list)
        assert all(isinstance(item, EvidenceMapItem) for item in result)

    def test_one_item_per_requirement(self):
        extraction = _extraction("req one", "req two", "req three")
        result = build_evidence_map(extraction)
        assert len(result) == 3

    def test_requirement_id_preserved(self):
        extraction = [{"id": "R42", "text": "Some text.", "level": ""}]
        result = build_evidence_map(extraction)
        assert result[0].requirement_id == "R42"

    def test_empty_extraction_returns_empty(self):
        assert build_evidence_map([]) == []


# ---------------------------------------------------------------------------
# Artifact mapping — individual keywords
# ---------------------------------------------------------------------------

class TestInsuranceMapping:
    def test_artifacts(self):
        assert "Insurance Certificate (PDF)" in _artifacts_for(
            "The supplier must hold valid public liability insurance."
        )

    def test_evidence_needed(self):
        assert "insurance" in _evidence_for(
            "The supplier must hold valid public liability insurance."
        )


class TestTaxMapping:
    def test_tax_clearance_in_text(self):
        assert "Tax Clearance / Revenue Statement" in _artifacts_for(
            "A current tax clearance certificate must be submitted."
        )

    def test_revenue_keyword(self):
        assert "Tax Clearance / Revenue Statement" in _artifacts_for(
            "Certificate from Revenue must be provided."
        )

    def test_evidence_needed(self):
        assert "tax clearance" in _evidence_for(
            "A current tax clearance certificate must be submitted."
        )


class TestPolicyMapping:
    def test_artifacts(self):
        assert "Relevant Policy Document (DOCX/PDF)" in _artifacts_for(
            "A copy of the company data protection policy must be provided."
        )

    def test_evidence_needed(self):
        assert "policy" in _evidence_for(
            "A copy of the company data protection policy must be provided."
        )


class TestCvExperienceMapping:
    def test_cv_keyword(self):
        arts = _artifacts_for("Staff CVs and qualifications must be submitted.")
        assert "Staff CVs" in arts
        assert "Case Studies" in arts

    def test_experience_keyword(self):
        arts = _artifacts_for("5 years experience in the sector required.")
        assert "Staff CVs" in arts
        assert "Case Studies" in arts

    def test_evidence_needed_cv(self):
        ev = _evidence_for("Staff CV must be provided.")
        assert "cv" in ev


class TestMethodStatementMapping:
    def test_artifacts(self):
        assert "Method Statement" in _artifacts_for(
            "A method statement for service delivery must be included."
        )

    def test_evidence_needed(self):
        assert "method statement" in _evidence_for(
            "A method statement for service delivery must be included."
        )


class TestRiskAssessmentMapping:
    def test_risk_assessment_keyword(self):
        assert "Risk Assessment" in _artifacts_for(
            "A risk assessment must be submitted before commencement."
        )

    def test_rams_keyword(self):
        assert "Risk Assessment" in _artifacts_for(
            "Current RAMS documentation must be provided."
        )

    def test_evidence_needed(self):
        assert "risk assessment" in _evidence_for(
            "A risk assessment must be submitted."
        )


# ---------------------------------------------------------------------------
# Fallback to "Supporting Document"
# ---------------------------------------------------------------------------

class TestFallback:
    def test_unmatched_text(self):
        arts = _artifacts_for("Pricing information to be submitted per the schedule.")
        assert arts == ["Supporting Document"]

    def test_empty_evidence_needed_when_no_match(self):
        ev = _evidence_for("Pricing information to be submitted per the schedule.")
        assert ev == []


# ---------------------------------------------------------------------------
# Multi-keyword requirement
# ---------------------------------------------------------------------------

class TestMultiKeyword:
    def test_insurance_and_policy_combined(self):
        arts = _artifacts_for(
            "The supplier must hold insurance and provide a data protection policy."
        )
        assert "Insurance Certificate (PDF)" in arts
        assert "Relevant Policy Document (DOCX/PDF)" in arts

    def test_no_duplicate_artifacts(self):
        # Two separate insurance mentions should not duplicate the artifact
        arts = _artifacts_for(
            "Public liability insurance and employer's liability insurance required."
        )
        assert arts.count("Insurance Certificate (PDF)") == 1


# ---------------------------------------------------------------------------
# Full fixture smoke test
# ---------------------------------------------------------------------------

class TestFixture:
    def test_all_requirements_covered(self, extraction_01):
        result = build_evidence_map(extraction_01)
        assert len(result) == len(extraction_01)

    def test_insurance_req_mapped(self, extraction_01):
        items = build_evidence_map(extraction_01)
        insurance_items = [
            item for item in items
            if "Insurance Certificate (PDF)" in item.suggested_artifacts
        ]
        assert len(insurance_items) >= 1

    def test_risk_assessment_req_mapped(self, extraction_01):
        items = build_evidence_map(extraction_01)
        risk_items = [
            item for item in items
            if "Risk Assessment" in item.suggested_artifacts
        ]
        assert len(risk_items) >= 1
