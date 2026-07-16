from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

def now(): return datetime.now(timezone.utc)
class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120)); email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True); company_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True); enquiry: Mapped[str] = mapped_column(Text)
    estimated_budget: Mapped[str | None] = mapped_column(String(80), nullable=True); preferred_timeline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True); detected_service: Mapped[str | None] = mapped_column(String(160), nullable=True)
    business_need: Mapped[str | None] = mapped_column(Text, nullable=True); urgency: Mapped[str | None] = mapped_column(String(80), nullable=True)
    budget_category: Mapped[str | None] = mapped_column(String(80), nullable=True); lead_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lead_status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True); recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    personalized_reply: Mapped[str | None] = mapped_column(Text, nullable=True); workflow_status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    workflow_result: Mapped[str | None] = mapped_column(Text, nullable=True); follow_up_status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
