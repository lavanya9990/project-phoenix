import json
from app.schemas import Analysis, FactCheck, Source
from app.services.llm_service import LLMService

def run(analysis: Analysis, sources: list[Source]) -> FactCheck:
    payload = json.dumps([x.model_dump() for x in sources])
    return LLMService().structured("Check claims strictly against supplied sources. Never invent URLs. Return valid JSON.", f"Analysis: {analysis.model_dump_json()}\nSources: {payload}\nShape: {{\"claims\": [{{\"claim\": str, \"status\": \"supported|uncertain|unsupported\", \"explanation\": str, \"source_urls\": [str]}}]}}", FactCheck)
