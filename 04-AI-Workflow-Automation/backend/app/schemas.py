from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field
LeadStatus = Literal["Hot", "Warm", "Cold"]
class LeadCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120); email: EmailStr
    phone: str | None = None; company_name: str | None = None; business_type: str | None = None
    enquiry: str = Field(min_length=10, max_length=5000); estimated_budget: str | None = None; preferred_timeline: str | None = None
class AIAnalysis(BaseModel):
    summary: str; detected_service: str; business_need: str; urgency: str; budget_category: str
    lead_score: int = Field(ge=0, le=100); lead_status: LeadStatus; recommended_action: str; personalized_reply: str
class LeadUpdate(BaseModel):
    lead_status: LeadStatus | None = None; follow_up_status: Literal["pending","scheduled","completed","cancelled"] | None = None; recommended_action: str | None = None
class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; full_name: str; email: EmailStr; phone: str | None; company_name: str | None; business_type: str | None; enquiry: str
    estimated_budget: str | None; preferred_timeline: str | None; ai_summary: str | None; detected_service: str | None; business_need: str | None
    urgency: str | None; budget_category: str | None; lead_score: int | None; lead_status: str | None; recommended_action: str | None
    personalized_reply: str | None; workflow_status: str; workflow_result: str | None; follow_up_status: str; created_at: datetime; updated_at: datetime; error_message: str | None
class DashboardStats(BaseModel):
    total_leads: int; hot_leads: int; warm_leads: int; cold_leads: int; completed_workflows: int; failed_workflows: int; pending_follow_ups: int; recent_leads: list[LeadRead]
