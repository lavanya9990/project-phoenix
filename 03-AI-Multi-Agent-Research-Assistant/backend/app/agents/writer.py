from app.schemas import Analysis, FactCheck, FinalReport
from app.services.llm_service import LLMService

def run(topic: str, analysis: Analysis, checked: FactCheck) -> FinalReport:
    return LLMService().structured("Write from supported claims, qualify uncertainty, omit unsupported claims, and return valid JSON.", f"Topic: {topic}\nAnalysis: {analysis.model_dump_json()}\nFact check: {checked.model_dump_json()}\nShape: {{\"title\": str, \"executive_summary\": str, \"key_findings\": [str], \"detailed_analysis\": str, \"risks_and_limitations\": [str], \"conclusion\": str}}", FinalReport)
