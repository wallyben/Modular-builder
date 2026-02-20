from __future__ import annotations

from pathlib import Path

import pytest

from modules.tender.hardening import TenderExtraction

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_extraction(filename: str) -> TenderExtraction:
    lines = (FIXTURES_DIR / filename).read_text().splitlines()
    lines = [ln.strip() for ln in lines if ln.strip()]
    return [{"id": str(i + 1), "text": line, "level": ""} for i, line in enumerate(lines)]


@pytest.fixture
def extraction_01() -> TenderExtraction:
    return _load_extraction("tender_text_01.txt")
