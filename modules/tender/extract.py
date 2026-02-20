from __future__ import annotations

from typing import Any, Callable, Optional

from modules.tender.schemas import Requirement, TenderExtraction

_FALLBACK_EXTRACTION = TenderExtraction(
    requirements=[
        Requirement(
            id="REQ-001",
            text="Adapter not configured — manual review required.",
            category="info",
            evidence_needed=[],
        )
    ]
)


def extract_requirements_from_text(
    text: str,
    adapter: Optional[Callable[[str], Any]] = None,
) -> TenderExtraction:
    """Extract requirements from tender text using the provided adapter.

    If *adapter* is None or falsy, a deterministic fallback is returned so the
    pipeline can continue without an LLM configured.
    """
    if not adapter:
        return _FALLBACK_EXTRACTION

    raw = adapter(text)
    if isinstance(raw, TenderExtraction):
        return raw
    return TenderExtraction.model_validate(raw)
