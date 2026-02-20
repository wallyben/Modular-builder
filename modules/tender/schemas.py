from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class EvidenceMapItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    evidence_needed: list[str]
    suggested_artifacts: list[str]


class DisqualifyFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Literal[
        "insurance",
        "tax_clearance",
        "health_safety",
        "financials",
        "experience",
        "other",
    ]
    requirement_id: Optional[str]
    message: str
