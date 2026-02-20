import os
import tempfile

from modules.tender.export import export_win_pack_docx
from modules.tender.matrix import build_compliance_matrix
from modules.tender.schemas import (
    ComplianceRow,
    CoverageSummary,
    EvidenceGap,
    Requirement,
    TenderExtraction,
    TenderMatrix,
)
from modules.tender.scoring import identify_evidence_gaps, score_matrix


def _make_extraction() -> TenderExtraction:
    return TenderExtraction(
        requirements=[
            Requirement(
                id="REQ-001",
                text="Supplier must hold ISO 9001 certification.",
                category="mandatory",
                evidence_needed=["ISO certificate"],
            ),
            Requirement(
                id="REQ-002",
                text="Provide methodology plan.",
                category="rated",
                evidence_needed=["methodology.pdf"],
            ),
        ]
    )


def _make_matrix() -> TenderMatrix:
    return TenderMatrix(
        rows=[
            ComplianceRow(requirement_id="REQ-001", status="met", notes="Attached"),
            ComplianceRow(requirement_id="REQ-002", status="missing", notes=""),
        ]
    )


class TestExportWinPackDocx:
    def test_file_created(self):
        extraction = _make_extraction()
        matrix = _make_matrix()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            out_path = f.name
        try:
            result = export_win_pack_docx(out_path, "tender text", extraction, matrix, None, None)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
        finally:
            os.unlink(out_path)

    def test_returns_out_path(self):
        extraction = _make_extraction()
        matrix = _make_matrix()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            out_path = f.name
        try:
            result = export_win_pack_docx(out_path, "text", extraction, matrix, None, None)
            assert result == out_path
        finally:
            os.unlink(out_path)

    def test_with_summary_and_gaps(self):
        extraction = _make_extraction()
        matrix = _make_matrix()
        summary = score_matrix(matrix)
        gaps = identify_evidence_gaps(extraction, matrix)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            out_path = f.name
        try:
            result = export_win_pack_docx(out_path, "tender", extraction, matrix, summary, gaps)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
        finally:
            os.unlink(out_path)

    def test_long_tender_text_truncated(self):
        extraction = _make_extraction()
        matrix = _make_matrix()
        long_text = "A" * 10000
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            out_path = f.name
        try:
            result = export_win_pack_docx(out_path, long_text, extraction, matrix, None, None)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
        finally:
            os.unlink(out_path)

    def test_empty_matrix(self):
        extraction = TenderExtraction(requirements=[])
        matrix = TenderMatrix(rows=[])
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            out_path = f.name
        try:
            result = export_win_pack_docx(out_path, "text", extraction, matrix, None, None)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
        finally:
            os.unlink(out_path)
