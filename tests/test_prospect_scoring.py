from pathlib import Path

import pytest

from modules.prospecting.awards_extract import extract_award_notice
from modules.prospecting.schemas import AwardNotice, Prospect
from modules.prospecting.scoring import score_prospect

FIXTURE = Path(__file__).parent / "fixtures" / "award_notice_fm_01.txt"


@pytest.fixture()
def fm_notice() -> AwardNotice:
    text = FIXTURE.read_text(encoding="utf-8")
    return extract_award_notice(text)


@pytest.fixture()
def fm_prospect(fm_notice) -> Prospect:
    return score_prospect(fm_notice)


def test_returns_prospect(fm_prospect):
    assert isinstance(fm_prospect, Prospect)


def test_niche_is_fm(fm_prospect):
    assert fm_prospect.niche == "facilities_management"


def test_score_in_range(fm_prospect):
    assert 0 <= fm_prospect.score <= 100


def test_fm_fixture_scores_well(fm_prospect):
    # Fixture has cleaning, maintenance, grounds, M&E, HVAC, waste, security, pest — should score high
    assert fm_prospect.score >= 50


def test_rationale_not_empty(fm_prospect):
    assert len(fm_prospect.rationale) > 0


def test_company_name_set(fm_prospect):
    assert fm_prospect.company_name != ""


def test_non_fm_scores_low():
    notice = AwardNotice(
        source="manual-paste",
        title="Supply of Office Stationery and Paper Products",
        description="Provision of A4 paper, pens, and binders to government offices.",
        winner_name="OfficeStuff Ltd",
    )
    prospect = score_prospect(notice)
    assert prospect.score < 20


def test_score_capped_at_100():
    notice = AwardNotice(
        source="manual-paste",
        title="Integrated facilities management cleaning janitorial maintenance grounds M&E HVAC",
        description=(
            "Total facilities management services including cleaning, janitorial, "
            "grounds maintenance, M&E, HVAC, waste management, security, catering, "
            "pest control, mechanical, electrical, facilities services."
        ),
        winner_name="MegaFM Ltd",
    )
    prospect = score_prospect(notice)
    assert prospect.score <= 100
