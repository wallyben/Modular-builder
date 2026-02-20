from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class AwardNotice(BaseModel, extra="forbid"):
    source: str
    authority: str | None = None
    title: str | None = None
    description: str | None = None
    award_date: str | None = None
    value_eur: float | None = None
    winner_name: str | None = None


class Prospect(BaseModel, extra="forbid"):
    company_name: str
    niche: Literal["facilities_management"]
    authority: str | None = None
    contract_title: str | None = None
    award_date: str | None = None
    value_eur: float | None = None
    score: int
    rationale: list[str]


class OutreachDraft(BaseModel, extra="forbid"):
    company_name: str
    subject: str
    email_1: str
    followup_1: str
    followup_2: str
    loom_script: str
