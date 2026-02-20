"""Tests for detect_disqualify_flags in modules/tender/hardening.py"""
from __future__ import annotations

import pytest

from modules.tender.hardening import TenderExtraction, detect_disqualify_flags
from modules.tender.schemas import DisqualifyFlag


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extraction(*texts: str) -> TenderExtraction:
    return [{"id": str(i + 1), "text": t, "level": ""} for i, t in enumerate(texts)]


def _flags_for(*texts: str) -> list[DisqualifyFlag]:
    return detect_disqualify_flags(_extraction(*texts))


def _codes_for(*texts: str) -> list[str]:
    return [f.code for f in _flags_for(*texts)]


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

class TestReturnType:
    def test_returns_list(self):
        assert isinstance(detect_disqualify_flags([]), list)

    def test_returns_disqualify_flag_instances(self):
        flags = _flags_for("The supplier must hold valid insurance.")
        assert all(isinstance(f, DisqualifyFlag) for f in flags)

    def test_empty_extraction_no_flags(self):
        assert detect_disqualify_flags([]) == []

    def test_no_match_text_no_flags(self):
        flags = _flags_for("Pricing information to be submitted per the schedule.")
        assert flags == []


# ---------------------------------------------------------------------------
# Insurance flag
# ---------------------------------------------------------------------------

class TestInsuranceFlag:
    def test_insurance_detected(self):
        assert "insurance" in _codes_for(
            "The supplier must hold valid public liability insurance of €6.5m."
        )

    def test_requirement_id_set(self):
        flags = _flags_for("The supplier must hold valid insurance.")
        ins_flags = [f for f in flags if f.code == "insurance"]
        assert ins_flags[0].requirement_id == "1"

    def test_message_populated(self):
        flags = _flags_for("The supplier must hold valid insurance.")
        ins_flags = [f for f in flags if f.code == "insurance"]
        assert ins_flags[0].message != ""


# ---------------------------------------------------------------------------
# Tax clearance flag
# ---------------------------------------------------------------------------

class TestTaxClearanceFlag:
    def test_tax_clearance_keyword(self):
        assert "tax_clearance" in _codes_for(
            "A current tax clearance certificate must be submitted."
        )

    def test_revenue_keyword(self):
        assert "tax_clearance" in _codes_for(
            "Certificate from Revenue must be provided."
        )

    def test_requirement_id_set(self):
        flags = _flags_for("A tax clearance certificate from Revenue is required.")
        tc_flags = [f for f in flags if f.code == "tax_clearance"]
        assert tc_flags[0].requirement_id == "1"

    def test_plain_tax_alone_not_flagged(self):
        # "tax" alone does not trigger tax_clearance (requires "tax clearance" or "revenue")
        codes = _codes_for("The tax rate applicable is 23%.")
        assert "tax_clearance" not in codes


# ---------------------------------------------------------------------------
# Health & safety flag
# ---------------------------------------------------------------------------

class TestHealthSafetyFlag:
    def test_safety_statement_keyword(self):
        assert "health_safety" in _codes_for(
            "A current safety statement must be provided."
        )

    def test_rams_keyword(self):
        assert "health_safety" in _codes_for(
            "Current RAMS documentation must be submitted."
        )

    def test_risk_assessment_keyword(self):
        assert "health_safety" in _codes_for(
            "A risk assessment must be completed before work commences."
        )

    def test_requirement_id_correct(self):
        # Second requirement triggers health_safety
        flags = _flags_for(
            "Insurance is required.",
            "A risk assessment must be provided.",
        )
        hs_flags = [f for f in flags if f.code == "health_safety"]
        assert hs_flags[0].requirement_id == "2"


# ---------------------------------------------------------------------------
# Financials flag
# ---------------------------------------------------------------------------

class TestFinancialsFlag:
    def test_audited_accounts_keyword(self):
        assert "financials" in _codes_for(
            "Audited accounts for the last three years must be submitted."
        )

    def test_turnover_keyword(self):
        assert "financials" in _codes_for(
            "Minimum annual turnover of €500,000 is required."
        )

    def test_requirement_id_set(self):
        flags = _flags_for("Audited accounts must be supplied.")
        fin_flags = [f for f in flags if f.code == "financials"]
        assert fin_flags[0].requirement_id == "1"


# ---------------------------------------------------------------------------
# Experience flag
# ---------------------------------------------------------------------------

class TestExperienceFlag:
    def test_minimum_years_experience(self):
        assert "experience" in _codes_for(
            "The supplier shall demonstrate a minimum of 5 years experience."
        )

    def test_years_experience_phrase(self):
        assert "experience" in _codes_for(
            "Bidders must have 3 years experience in the field."
        )

    def test_minimum_experience_phrase(self):
        assert "experience" in _codes_for(
            "Minimum experience of 5 years in similar projects is required."
        )

    def test_requirement_id_set(self):
        flags = _flags_for(
            "The supplier shall demonstrate a minimum of 5 years experience."
        )
        exp_flags = [f for f in flags if f.code == "experience"]
        assert exp_flags[0].requirement_id == "1"


# ---------------------------------------------------------------------------
# Multiple flags from one requirement
# ---------------------------------------------------------------------------

class TestMultipleFlags:
    def test_insurance_and_tax_in_one_req(self):
        codes = _codes_for(
            "The supplier must hold insurance and provide a tax clearance from Revenue."
        )
        assert "insurance" in codes
        assert "tax_clearance" in codes

    def test_flags_carry_same_requirement_id(self):
        flags = _flags_for(
            "The supplier must hold insurance and provide a tax clearance from Revenue."
        )
        req_ids = {f.requirement_id for f in flags}
        assert req_ids == {"1"}


# ---------------------------------------------------------------------------
# requirement_id is None only when not identifiable
# ---------------------------------------------------------------------------

class TestRequirementId:
    def test_requirement_id_none_not_present_when_matched(self):
        flags = _flags_for("Valid insurance required.")
        for f in flags:
            assert f.requirement_id is not None


# ---------------------------------------------------------------------------
# Full fixture smoke test
# ---------------------------------------------------------------------------

class TestFixture:
    def test_insurance_flag_present(self, extraction_01):
        codes = [f.code for f in detect_disqualify_flags(extraction_01)]
        assert "insurance" in codes

    def test_tax_clearance_flag_present(self, extraction_01):
        codes = [f.code for f in detect_disqualify_flags(extraction_01)]
        assert "tax_clearance" in codes

    def test_health_safety_flag_present(self, extraction_01):
        codes = [f.code for f in detect_disqualify_flags(extraction_01)]
        assert "health_safety" in codes

    def test_financials_flag_present(self, extraction_01):
        codes = [f.code for f in detect_disqualify_flags(extraction_01)]
        assert "financials" in codes

    def test_experience_flag_present(self, extraction_01):
        codes = [f.code for f in detect_disqualify_flags(extraction_01)]
        assert "experience" in codes

    def test_all_flags_have_requirement_ids(self, extraction_01):
        flags = detect_disqualify_flags(extraction_01)
        assert all(f.requirement_id is not None for f in flags)
