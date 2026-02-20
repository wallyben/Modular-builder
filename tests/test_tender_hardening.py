"""Tests for modules/tender/hardening.py"""
import pytest
from modules.tender.hardening import (
    GENERIC_PHRASES,
    calculate_split_scores,
    classify_requirement_levels,
    detect_generic_language,
    detect_mandatory_gaps,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

EXTRACTION = [
    {"id": "R1", "text": "The supplier must provide 24/7 support.", "level": ""},
    {"id": "R2", "text": "The solution shall be ISO 27001 certified.", "level": ""},
    {"id": "R3", "text": "The system should offer API access.", "level": ""},
    {"id": "R4", "text": "The vendor may provide training.", "level": ""},
    {"id": "R5", "text": "Pricing information to be supplied separately.", "level": ""},
]

MATRIX = [
    {"requirement_id": "R1", "status": "met"},
    {"requirement_id": "R2", "status": "not_met"},
    {"requirement_id": "R3", "status": "partial"},
    {"requirement_id": "R4", "status": "met"},
    {"requirement_id": "R5", "status": ""},
]


# ---------------------------------------------------------------------------
# 1) classify_requirement_levels
# ---------------------------------------------------------------------------

class TestClassifyRequirementLevels:
    def test_mandatory_detected(self):
        result = classify_requirement_levels(EXTRACTION)
        assert "R1" in result["mandatory_ids"]  # "must"
        assert "R2" in result["mandatory_ids"]  # "shall"

    def test_rated_detected(self):
        result = classify_requirement_levels(EXTRACTION)
        assert "R3" in result["rated_ids"]  # "should"
        assert "R4" in result["rated_ids"]  # "may"

    def test_info_detected(self):
        result = classify_requirement_levels(EXTRACTION)
        assert "R5" in result["info_ids"]

    def test_returns_all_keys(self):
        result = classify_requirement_levels(EXTRACTION)
        assert set(result.keys()) == {"mandatory_ids", "rated_ids", "info_ids"}

    def test_empty_extraction(self):
        result = classify_requirement_levels([])
        assert result == {"mandatory_ids": [], "rated_ids": [], "info_ids": []}

    def test_total_count_matches(self):
        result = classify_requirement_levels(EXTRACTION)
        total = (
            len(result["mandatory_ids"])
            + len(result["rated_ids"])
            + len(result["info_ids"])
        )
        assert total == len(EXTRACTION)


# ---------------------------------------------------------------------------
# 2) detect_mandatory_gaps
# ---------------------------------------------------------------------------

class TestDetectMandatoryGaps:
    def test_gap_detected(self):
        # R2 is mandatory and status is "not_met"
        gaps = detect_mandatory_gaps(MATRIX, ["R1", "R2"])
        assert "R2" in gaps

    def test_met_not_in_gaps(self):
        gaps = detect_mandatory_gaps(MATRIX, ["R1", "R2"])
        assert "R1" not in gaps

    def test_empty_mandatory_ids(self):
        assert detect_mandatory_gaps(MATRIX, []) == []

    def test_all_met(self):
        matrix = [
            {"requirement_id": "R1", "status": "met"},
            {"requirement_id": "R2", "status": "met"},
        ]
        assert detect_mandatory_gaps(matrix, ["R1", "R2"]) == []

    def test_partial_counts_as_gap(self):
        matrix = [{"requirement_id": "X1", "status": "partial"}]
        gaps = detect_mandatory_gaps(matrix, ["X1"])
        assert "X1" in gaps

    def test_non_mandatory_ids_ignored(self):
        # R3 is not in mandatory_ids, so even if not_met it should not appear
        gaps = detect_mandatory_gaps(MATRIX, ["R1"])
        assert "R3" not in gaps


# ---------------------------------------------------------------------------
# 3) detect_generic_language
# ---------------------------------------------------------------------------

class TestDetectGenericLanguage:
    def test_phrase_found(self):
        text = "We are a world class provider of best in class solutions."
        found = detect_generic_language(text)
        assert "world class" in found
        assert "best in class" in found

    def test_case_insensitive(self):
        text = "We offer INDUSTRY-LEADING and State Of The Art technology."
        found = detect_generic_language(text)
        assert "industry-leading" in found
        assert "state of the art" in found

    def test_no_match(self):
        text = "We provide compliant, evidence-based services."
        assert detect_generic_language(text) == []

    def test_all_phrases_detectable(self):
        text = " ".join(GENERIC_PHRASES)
        found = detect_generic_language(text)
        assert set(found) == set(GENERIC_PHRASES)

    def test_empty_string(self):
        assert detect_generic_language("") == []


# ---------------------------------------------------------------------------
# 4) calculate_split_scores
# ---------------------------------------------------------------------------

class TestCalculateSplitScores:
    def setup_method(self):
        self.classification = {
            "mandatory_ids": ["R1", "R2"],  # R1=met(1.0), R2=not_met(0.0) → 0.5
            "rated_ids": ["R3", "R4"],      # R3=partial(0.5), R4=met(1.0) → 0.75
            "info_ids": ["R5"],
        }

    def test_mandatory_score(self):
        result = calculate_split_scores(MATRIX, self.classification)
        assert result["mandatory_score"] == pytest.approx(0.5)

    def test_rated_score(self):
        result = calculate_split_scores(MATRIX, self.classification)
        assert result["rated_score"] == pytest.approx(0.75)

    def test_returns_both_keys(self):
        result = calculate_split_scores(MATRIX, self.classification)
        assert set(result.keys()) == {"mandatory_score", "rated_score"}

    def test_empty_mandatory_returns_zero(self):
        classification = {"mandatory_ids": [], "rated_ids": ["R1"], "info_ids": []}
        matrix = [{"requirement_id": "R1", "status": "met"}]
        result = calculate_split_scores(matrix, classification)
        assert result["mandatory_score"] == 0.0

    def test_all_met_gives_one(self):
        matrix = [
            {"requirement_id": "A", "status": "met"},
            {"requirement_id": "B", "status": "met"},
        ]
        classification = {"mandatory_ids": ["A", "B"], "rated_ids": [], "info_ids": []}
        result = calculate_split_scores(matrix, classification)
        assert result["mandatory_score"] == pytest.approx(1.0)

    def test_partial_scores_half(self):
        matrix = [{"requirement_id": "A", "status": "partial"}]
        classification = {"mandatory_ids": ["A"], "rated_ids": [], "info_ids": []}
        result = calculate_split_scores(matrix, classification)
        assert result["mandatory_score"] == pytest.approx(0.5)

    def test_unknown_status_scores_zero(self):
        matrix = [{"requirement_id": "A", "status": "not_met"}]
        classification = {"mandatory_ids": ["A"], "rated_ids": [], "info_ids": []}
        result = calculate_split_scores(matrix, classification)
        assert result["mandatory_score"] == pytest.approx(0.0)
