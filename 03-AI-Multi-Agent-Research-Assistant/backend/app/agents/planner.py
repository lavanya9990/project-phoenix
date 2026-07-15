from app.schemas import ResearchPlan
from app.services.llm_service import LLMService

def run(topic: str, depth: str) -> ResearchPlan:
    count = {"quick": 3, "standard": 5, "deep": 8}[depth]
    return LLMService().structured("You are a research planner. Return only valid JSON.", f"Create a focused plan for '{topic}' with exactly {count} questions. Shape: {{\"title\": str, \"questions\": [{{\"question\": str, \"rationale\": str}}]}}", ResearchPlan)
