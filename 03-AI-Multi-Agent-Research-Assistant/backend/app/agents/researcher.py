from app.schemas import Finding, PlanItem, Source
from app.services.search_service import SearchService

def run(plan: list[PlanItem], depth: str) -> tuple[list[Source], list[Finding]]:
    limit = {"quick": 2, "standard": 3, "deep": 5}[depth]
    unique: dict[str, Source] = {}
    findings: list[Finding] = []
    search = SearchService()
    for item in plan:
        results = search.search(item.question, limit)
        for source in results:
            unique.setdefault(source.url.rstrip("/"), source)
        if results:
            findings.append(Finding(claim=f"Research material collected for: {item.question}", source_urls=[x.url for x in results]))
    if not unique:
        raise RuntimeError("Tavily returned no usable sources")
    return list(unique.values()), findings
