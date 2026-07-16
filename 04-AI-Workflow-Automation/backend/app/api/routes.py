from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models import Lead
from app.schemas import DashboardStats, LeadCreate, LeadRead, LeadUpdate
from app.services.lead_service import create_qualified_lead
router=APIRouter(prefix="/api")
@router.post("/leads",response_model=LeadRead,status_code=201)
async def create_lead(data:LeadCreate,db:Session=Depends(get_db)): return await create_qualified_lead(db,data,get_settings())
@router.get("/leads",response_model=list[LeadRead])
def list_leads(lead_status:str|None=None,business_type:str|None=None,workflow_status:str|None=None,q:str|None=Query(None,max_length=120),db:Session=Depends(get_db)):
    stmt=select(Lead).order_by(Lead.created_at.desc())
    if lead_status: stmt=stmt.where(Lead.lead_status==lead_status)
    if business_type: stmt=stmt.where(Lead.business_type==business_type)
    if workflow_status: stmt=stmt.where(Lead.workflow_status==workflow_status)
    if q:
        term=f"%{q}%"; stmt=stmt.where(or_(Lead.full_name.ilike(term),Lead.email.ilike(term),Lead.company_name.ilike(term),Lead.enquiry.ilike(term)))
    return list(db.scalars(stmt))
def find(lead_id:int,db:Session):
    lead=db.get(Lead,lead_id)
    if not lead: raise HTTPException(404,"Lead not found")
    return lead
@router.get("/leads/{lead_id}",response_model=LeadRead)
def get_lead(lead_id:int,db:Session=Depends(get_db)): return find(lead_id,db)
@router.patch("/leads/{lead_id}",response_model=LeadRead)
def update_lead(lead_id:int,data:LeadUpdate,db:Session=Depends(get_db)):
    lead=find(lead_id,db)
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(lead,k,v)
    db.commit(); db.refresh(lead); return lead
@router.delete("/leads/{lead_id}",status_code=204)
def delete_lead(lead_id:int,db:Session=Depends(get_db)): db.delete(find(lead_id,db)); db.commit(); return Response(status_code=204)
@router.get("/dashboard/stats",response_model=DashboardStats)
def stats(db:Session=Depends(get_db)):
    count=lambda condition: db.scalar(select(func.count()).select_from(Lead).where(condition)) or 0
    return DashboardStats(total_leads=count(Lead.id>0),hot_leads=count(Lead.lead_status=="Hot"),warm_leads=count(Lead.lead_status=="Warm"),cold_leads=count(Lead.lead_status=="Cold"),completed_workflows=count(Lead.workflow_status=="completed"),failed_workflows=count(Lead.workflow_status=="failed"),pending_follow_ups=count(Lead.follow_up_status=="pending"),recent_leads=list(db.scalars(select(Lead).order_by(Lead.created_at.desc()).limit(5))))
