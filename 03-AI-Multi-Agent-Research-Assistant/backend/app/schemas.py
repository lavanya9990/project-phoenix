from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Depth = Literal["quick", "standard", "deep"]


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    research_depth: Depth = "standard"


class PlanItem(BaseModel):
    question: str
    rationale: str


class ResearchPlan(BaseModel):
    title: str
    questions: list[PlanItem]


class Source(BaseModel):
    title: str
    url: str
    snippet: str
    research_question: str


class Finding(BaseModel):
    claim: str
    source_urls: list[str]


class Analysis(BaseModel):
    facts: list[str]
    interpretations: list[str]
    patterns: list[str]
    risks: list[str]
    opportunities: list[str]


class CheckedClaim(BaseModel):
    claim: str
    status: Literal["supported", "uncertain", "unsupported"]
    explanation: str
    source_urls: list[str]


class FactCheck(BaseModel):
    claims: list[CheckedClaim]


class FinalReport(BaseModel):
    title: str
    executive_summary: str
    key_findings: list[str]
    detailed_analysis: str
    risks_and_limitations: list[str]
    conclusion: str


class ResearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    research_id: int
    topic: str
    status: str
    research_depth: Depth
    plan: list[PlanItem] = []
    sources: list[Source] = []
    final_report: str = ""
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
