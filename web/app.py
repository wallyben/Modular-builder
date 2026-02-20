from __future__ import annotations

import tempfile
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from modules.tender.hardening import (
    TenderExtraction,
    TenderMatrix,
    build_evidence_map,
    calculate_split_scores,
    classify_requirement_levels,
    detect_disqualify_flags,
    detect_mandatory_gaps,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Modular Builder — Internal UI")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ---------------------------------------------------------------------------
# Domain stubs — wire to real implementations when available
# ---------------------------------------------------------------------------

def extract_requirements_from_text(text: str) -> list[str]:
    """Return requirement strings extracted from raw tender text."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines[:20] if lines else ["(no requirements extracted)"]


def build_compliance_matrix(requirements: list[str]) -> list[Dict[str, Any]]:
    """Map each requirement to a compliance row."""
    return [
        {"id": i + 1, "requirement": req, "compliant": None, "evidence": ""}
        for i, req in enumerate(requirements)
    ]


def score_matrix(matrix: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a summary score for the compliance matrix."""
    total = len(matrix)
    return {
        "total": total,
        "compliant": 0,
        "non_compliant": 0,
        "unknown": total,
        "score_pct": 0,
    }


def identify_evidence_gaps(matrix: list[Dict[str, Any]]) -> list[str]:
    """Return list of requirements lacking evidence."""
    return [row["requirement"] for row in matrix if not row.get("evidence")]


def fetch_award_text(url: str) -> str:
    """Fetch and return raw text from an award notice URL."""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="replace")[:8000]
    except Exception as exc:
        return f"(could not fetch URL: {exc})"


def extract_award_notice(raw: str) -> Dict[str, Any]:
    """Parse key fields from raw award notice text."""
    return {
        "buyer": "(buyer not extracted)",
        "value": "(value not extracted)",
        "supplier": "(supplier not extracted)",
        "date": "(date not extracted)",
        "description": raw[:500] if raw else "(empty)",
    }


def score_prospect(notice: Dict[str, Any]) -> Dict[str, Any]:
    """Return a fit score for the prospect."""
    return {
        "fit_score": 0,
        "max_score": 100,
        "rationale": "Scoring model not yet configured.",
    }


def draft_outreach(notice: Dict[str, Any], score: Dict[str, Any]) -> str:
    """Draft an outreach message for the prospect."""
    return (
        "Dear team,\n\n"
        "We noted a recent award relevant to your needs. "
        "Please find our initial outreach attached.\n\n"
        "Regards,\nModular Builder"
    )


# ---------------------------------------------------------------------------
# In-memory result store (request-scoped via app.state for simplicity)
# ---------------------------------------------------------------------------

_last_tender: Dict[str, Any] = {}
_last_prospect: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Routes — Tender
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/tender", response_class=HTMLResponse)
async def tender_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("tender.html", {"request": request})


@app.post("/tender", response_class=HTMLResponse)
async def tender_submit(request: Request, file: UploadFile = File(...)) -> HTMLResponse:
    if not file.filename.endswith(".txt"):
        return templates.TemplateResponse(
            "tender.html",
            {"request": request, "error": "Only .txt files are accepted."},
            status_code=422,
        )

    raw = (await file.read()).decode("utf-8", errors="replace")

    requirements = extract_requirements_from_text(raw)
    matrix = build_compliance_matrix(requirements)
    score = score_matrix(matrix)
    gaps = identify_evidence_gaps(matrix)

    # --- Hardening layer ---
    extraction: TenderExtraction = [
        {"id": str(row["id"]), "text": row["requirement"], "level": ""}
        for row in matrix
    ]
    tender_matrix: TenderMatrix = [
        {"requirement_id": str(row["id"]), "status": row.get("status", "")}
        for row in matrix
    ]
    classification = classify_requirement_levels(extraction)
    mandatory_gaps = detect_mandatory_gaps(tender_matrix, classification["mandatory_ids"])
    split_scores = calculate_split_scores(tender_matrix, classification)
    evidence_map = build_evidence_map(extraction)
    disqualify_flags = detect_disqualify_flags(extraction)

    global _last_tender
    _last_tender = {"requirements": requirements, "matrix": matrix, "score": score, "gaps": gaps}

    return templates.TemplateResponse(
        "result_tender.html",
        {
            "request": request,
            "requirements": requirements,
            "matrix": matrix,
            "score": score,
            "gaps": gaps,
            "classification": classification,
            "mandatory_gaps": mandatory_gaps,
            "split_scores": split_scores,
            "evidence_map": evidence_map,
            "disqualify_flags": disqualify_flags,
        },
    )


# ---------------------------------------------------------------------------
# Routes — Prospect
# ---------------------------------------------------------------------------

@app.get("/prospect", response_class=HTMLResponse)
async def prospect_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("prospect.html", {"request": request})


@app.post("/prospect", response_class=HTMLResponse)
async def prospect_submit(request: Request, url: str = Form(...)) -> HTMLResponse:
    raw = fetch_award_text(url)
    notice = extract_award_notice(raw)
    score = score_prospect(notice)
    outreach = draft_outreach(notice, score)

    global _last_prospect
    _last_prospect = {"url": url, "notice": notice, "score": score, "outreach": outreach}

    return templates.TemplateResponse(
        "result_prospect.html",
        {
            "request": request,
            "url": url,
            "notice": notice,
            "score": score,
            "outreach": outreach,
        },
    )


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

@app.get("/download-docx")
async def download_docx() -> FileResponse:
    try:
        from docx import Document  # type: ignore
        doc = Document()
        doc.add_heading("Tender Compliance Report", 0)

        score = _last_tender.get("score", {})
        doc.add_paragraph(
            f"Score: {score.get('compliant', 0)}/{score.get('total', 0)} "
            f"({score.get('score_pct', 0)}%)"
        )

        doc.add_heading("Requirements", level=1)
        for row in _last_tender.get("matrix", []):
            doc.add_paragraph(f"[{row['id']}] {row['requirement']}", style="List Bullet")

        doc.add_heading("Evidence Gaps", level=1)
        for gap in _last_tender.get("gaps", []):
            doc.add_paragraph(gap, style="List Bullet")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(tmp.name)
        tmp.close()
        return FileResponse(
            tmp.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="tender_report.docx",
        )
    except ImportError:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            "python-docx is not installed. Run: pip install python-docx",
            status_code=501,
        )
