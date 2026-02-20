from __future__ import annotations

from typing import Any, Optional

from modules.tender.extract import extract_requirements_from_text
from modules.tender.matrix import build_compliance_matrix
from modules.tender.scoring import identify_evidence_gaps, score_matrix

_DEMO_TENDER_TEXT = """\
TENDER FOR PROFESSIONAL SERVICES — INFRASTRUCTURE UPGRADE PROJECT
Reference: GOV-2024-INFRA-009
Closing Date: 30 days from issue

SECTION 1 — MANDATORY REQUIREMENTS

1.1  The Contractor must hold a valid ISO 9001:2015 quality management certification.
     Evidence required: current ISO certificate (not older than 12 months).

1.2  The Contractor must demonstrate a minimum of five (5) years' experience
     delivering infrastructure projects of comparable scale.
     Evidence required: client references, project summaries.

1.3  The Contractor must carry professional indemnity insurance of no less than
     AUD 5,000,000 per occurrence.
     Evidence required: certificate of currency.

1.4  All sub-contractors must be disclosed prior to contract execution.
     Evidence required: sub-contractor register.

SECTION 2 — RATED CRITERIA

2.1  Project Methodology (30 points)
     Tenderers must submit a methodology document detailing approach, milestones,
     and risk-management framework.
     Evidence required: methodology document, risk register.

2.2  Key Personnel Qualifications (25 points)
     Provide CVs and professional registrations for all nominated key personnel.
     Evidence required: CVs, registration certificates.

2.3  Environmental & Sustainability Plan (20 points)
     Submit a plan outlining environmental controls and sustainability targets.
     Evidence required: environment plan.

2.4  Local Industry Participation (25 points)
     Describe how local suppliers and workforce will be engaged.
     Evidence required: local participation statement.

SECTION 3 — INFORMATION ONLY

3.1  Site inspections are available on request.  Contact the project manager
     at least 48 hours in advance.

3.2  All queries must be submitted in writing via the tender portal.
     No verbal responses will be binding.

3.3  The procuring entity reserves the right to accept or reject any tender.
"""


def generate_demo_tender_text() -> str:
    return _DEMO_TENDER_TEXT


def run_demo_flow(adapter: Optional[Any] = None) -> dict:
    text = generate_demo_tender_text()
    extraction = extract_requirements_from_text(text, adapter=adapter)
    matrix = build_compliance_matrix(extraction)
    summary = score_matrix(matrix)
    gaps = identify_evidence_gaps(extraction, matrix)
    return {
        "extraction": extraction,
        "matrix": matrix,
        "summary": summary,
        "gaps": gaps,
    }
