from modules.tender.demo import generate_demo_tender_text, run_demo_flow
from modules.tender.schemas import CoverageSummary, TenderExtraction, TenderMatrix


class TestGenerateDemoTenderText:
    def test_returns_non_empty_string(self):
        text = generate_demo_tender_text()
        assert isinstance(text, str)
        assert len(text) > 0


class TestRunDemoFlow:
    def setup_method(self):
        self.result = run_demo_flow(adapter=None)

    def test_returns_dict_with_expected_keys(self):
        assert set(self.result.keys()) == {"extraction", "matrix", "summary", "gaps"}

    def test_extraction_has_requirements(self):
        extraction = self.result["extraction"]
        assert isinstance(extraction, TenderExtraction)
        assert len(extraction.requirements) > 0

    def test_matrix_is_tender_matrix(self):
        assert isinstance(self.result["matrix"], TenderMatrix)

    def test_summary_score_between_0_and_1(self):
        summary = self.result["summary"]
        assert isinstance(summary, CoverageSummary)
        assert 0.0 <= summary.score <= 1.0

    def test_summary_total_matches_requirements(self):
        extraction = self.result["extraction"]
        summary = self.result["summary"]
        assert summary.total == len(extraction.requirements)

    def test_gaps_is_list(self):
        assert isinstance(self.result["gaps"], list)
