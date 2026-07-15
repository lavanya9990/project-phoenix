import json
from app.schemas import Analysis, Source
from app.services.llm_service import LLMService

def run(topic: str, sources: list[Source]) -> Analysis:
    payload = json.dumps([x.model_dump() for x in sources])
    return LLMService().structured("Analyze only supplied sources and separate facts from interpretation. Return valid JSON.", f"Topic: {topic}\nSources: {payload}\nShape: {{\"facts\": [str], \"interpretations\": [str], \"patterns\": [str], \"risks\": [str], \"opportunities\": [str]}}", Analysis)
