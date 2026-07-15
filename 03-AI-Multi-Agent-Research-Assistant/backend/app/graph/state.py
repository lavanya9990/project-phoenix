from typing import TypedDict

class ResearchState(TypedDict, total=False):
    topic: str
    research_depth: str
    plan: list[dict]
    research_questions: list[str]
    sources: list[dict]
    findings: list[dict]
    analysis: dict
    fact_check_results: dict
    final_report: dict
    current_step: str
    errors: list[str]
