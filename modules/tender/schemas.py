from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel


class Requirement(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    text: str
    category: Literal["mandatory", "rated", "info"]
    evidence_needed: List[str]


class TenderExtraction(BaseModel):
    model_config = {"extra": "forbid"}

    requirements: List[Requirement]


class ComplianceRow(BaseModel):
    model_config = {"extra": "forbid"}

    requirement_id: str
    status: Literal["unknown", "met", "partial", "missing"]
    notes: str


class TenderMatrix(BaseModel):
    model_config = {"extra": "forbid"}

    rows: List[ComplianceRow]
