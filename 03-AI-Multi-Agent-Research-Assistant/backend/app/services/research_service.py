import json
from sqlalchemy.orm import Session
from app.config import get_settings
from app.graph.workflow import workflow
from app.models import Research
from app.schemas import FinalReport, ResearchRequest, ResearchResponse

def markdown(report: FinalReport, sources: list[dict]) -> str:
    findings = "\n".join(f"- {x}" for x in report.key_findings)
    risks = "\n".join(f"- {x}" for x in report.risks_and_limitations)
    links = "\n".join(f"- [{x['title']}]({x['url']})" for x in sources)
    return f"# {report.title}\n\n## Executive Summary\n\n{report.executive_summary}\n\n## Key Findings\n\n{findings}\n\n## Detailed Analysis\n\n{report.detailed_analysis}\n\n## Risks and Limitations\n\n{risks}\n\n## Conclusion\n\n{report.conclusion}\n\n## Sources\n\n{links}"

def to_response(row: Research) -> ResearchResponse:
    return ResearchResponse(research_id=row.id, topic=row.topic, status=row.status, research_depth=row.research_depth, plan=json.loads(row.plan_json), sources=json.loads(row.sources_json), final_report=row.final_report, error_message=row.error_message, created_at=row.created_at, updated_at=row.updated_at)

def execute(db: Session, request: ResearchRequest) -> ResearchResponse:
    row = Research(topic=request.topic, research_depth=request.research_depth, status="running")
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        get_settings().validate_api_keys()
        state = workflow.invoke({"topic": request.topic, "research_depth": request.research_depth, "errors": [], "current_step": "starting"})
        report = FinalReport.model_validate(state["final_report"])
        row.plan_json = json.dumps(state["plan"])
        row.sources_json = json.dumps(state["sources"])
        row.final_report = markdown(report, state["sources"])
        row.status = "completed"
    except Exception as exc:
        row.status = "failed"
        row.error_message = str(exc)
    db.commit()
    db.refresh(row)
    return to_response(row)
