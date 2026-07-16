import json
from sqlalchemy.orm import Session
from app.config import Settings
from app.models import Lead
from app.schemas import LeadCreate
from app.services.ai_service import analyze_lead
from app.services.n8n_service import trigger_workflow
async def create_qualified_lead(db: Session, data: LeadCreate, settings: Settings):
    lead=Lead(**data.model_dump()); db.add(lead); db.commit(); db.refresh(lead)
    try:
        analysis=await analyze_lead(data,settings)
        for k,v in analysis.model_dump().items(): setattr(lead,"ai_summary" if k=="summary" else k,v)
        db.commit()
        payload={"lead_id":lead.id,"full_name":lead.full_name,"email":lead.email,"phone":lead.phone,"company_name":lead.company_name,"lead_status":lead.lead_status,"lead_score":lead.lead_score,"summary":lead.ai_summary,"recommended_action":lead.recommended_action,"personalized_reply":lead.personalized_reply}
        try: lead.workflow_status,result=await trigger_workflow(payload,settings); lead.workflow_result=json.dumps(result)
        except RuntimeError as exc: lead.workflow_status="failed"; lead.error_message=str(exc)
    except RuntimeError as exc: lead.workflow_status="skipped"; lead.error_message=str(exc)
    db.commit(); db.refresh(lead); return lead
