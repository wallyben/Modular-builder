from pathlib import Path

import pytest

from modules.prospecting.awards_extract import extract_award_notice
from modules.prospecting.outreach import draft_outreach
from modules.prospecting.schemas import OutreachDraft, Prospect
from modules.prospecting.scoring import score_prospect

FIXTURE = Path(__file__).parent / "fixtures" / "award_notice_fm_01.txt"


@pytest.fixture()
def prospect() -> Prospect:
    text = FIXTURE.read_text(encoding="utf-8")
    notice = extract_award_notice(text)
    return score_prospect(notice)


@pytest.fixture()
def draft(prospect) -> OutreachDraft:
    return draft_outreach(prospect)


def test_returns_outreach_draft(draft):
    assert isinstance(draft, OutreachDraft)


def test_company_name_in_draft(draft, prospect):
    assert draft.company_name == prospect.company_name


def test_subject_not_empty(draft):
    assert len(draft.subject) > 0


def test_email_1_not_empty(draft):
    assert len(draft.email_1) > 50


def test_followup_1_not_empty(draft):
    assert len(draft.followup_1) > 20


def test_followup_2_not_empty(draft):
    assert len(draft.followup_2) > 20


def test_loom_script_not_empty(draft):
    assert len(draft.loom_script) > 50


def test_no_guaranteed_wins_claim(draft):
    """Ensure draft makes no claims of guaranteed wins."""
    combined = " ".join([draft.email_1, draft.followup_1, draft.followup_2, draft.loom_script]).lower()
    forbidden = ["guarantee", "guaranteed win", "100% success", "certain to win"]
    for phrase in forbidden:
        assert phrase not in combined, f"Forbidden phrase found: '{phrase}'"


def test_large_value_mentioned_in_email(prospect):
    """Value above threshold should be mentioned in email_1."""
    high_value_prospect = Prospect(
        company_name=prospect.company_name,
        niche="facilities_management",
        authority=prospect.authority,
        contract_title=prospect.contract_title,
        award_date=prospect.award_date,
        value_eur=2_000_000.0,
        score=prospect.score,
        rationale=prospect.rationale,
    )
    d = draft_outreach(high_value_prospect)
    assert "€" in d.email_1 or "2.0m" in d.email_1.lower()


def test_unknown_company_fallback():
    prospect = Prospect(
        company_name="Unknown Company",
        niche="facilities_management",
        score=0,
        rationale=["No FM keywords matched"],
    )
    draft = draft_outreach(prospect)
    assert draft.company_name == "Unknown Company"
