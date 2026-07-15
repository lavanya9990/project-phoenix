from tavily import TavilyClient
from app.config import get_settings
from app.schemas import Source

class SearchService:
    def __init__(self) -> None:
        self.client = TavilyClient(api_key=get_settings().tavily_api_key)

    def search(self, question: str, max_results: int) -> list[Source]:
        try:
            response = self.client.search(query=question, search_depth="advanced", max_results=max_results)
        except Exception as exc:
            raise RuntimeError(f"Tavily search failed for: {question}") from exc
        return [Source(title=x.get("title") or x["url"], url=x["url"], snippet=x.get("content", ""), research_question=question) for x in response.get("results", []) if x.get("url")]
