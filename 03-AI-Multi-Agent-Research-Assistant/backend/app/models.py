from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Research(Base):
    __tablename__ = "research"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(500), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    research_depth: Mapped[str] = mapped_column(String(20))
    plan_json: Mapped[str] = mapped_column(Text, default="[]")
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    final_report: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
