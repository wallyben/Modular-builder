from pathlib import Path

import pytest

from modules.prospecting.awards_extract import extract_award_notice
from modules.prospecting.schemas import AwardNotice

FIXTURE = Path(__file__).parent / "fixtures" / "award_notice_fm_01.txt"


@pytest.fixture()
def sample_text() -> str:
    return FIXTURE.read_text(encoding="utf-8")


@pytest.fixture()
def notice(sample_text) -> AwardNotice:
    return extract_award_notice(sample_text)


def test_returns_award_notice(notice):
    assert isinstance(notice, AwardNotice)


def test_source_is_manual_paste(notice):
    assert notice.source == "manual-paste"


def test_winner_extracted(notice):
    assert notice.winner_name is not None
    assert "CleanCore" in notice.winner_name


def test_value_extracted(notice):
    assert notice.value_eur is not None
    assert notice.value_eur == pytest.approx(8_500_000, rel=0.01)


def test_authority_extracted(notice):
    assert notice.authority is not None
    assert len(notice.authority) > 2


def test_title_extracted(notice):
    assert notice.title is not None
    assert len(notice.title) > 5


def test_date_extracted(notice):
    assert notice.award_date is not None


def test_no_crash_on_empty_text():
    result = extract_award_notice("")
    assert isinstance(result, AwardNotice)
    assert result.winner_name is None
    assert result.value_eur is None


def test_no_crash_on_garbage_text():
    result = extract_award_notice("Lorem ipsum dolor sit amet.")
    assert isinstance(result, AwardNotice)
