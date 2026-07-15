from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Research
from app.schemas import ResearchRequest, ResearchResponse
from app.services.research_service import execute, to_response

router = APIRouter()

@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}

@router.post("/api/research", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
def create_research(request: ResearchRequest, db: Session = Depends(get_db)) -> ResearchResponse:
    return execute(db, request)

@router.get("/api/research", response_model=list[ResearchResponse])
def history(db: Session = Depends(get_db)) -> list[ResearchResponse]:
    rows = db.scalars(select(Research).order_by(Research.created_at.desc())).all()
    return [to_response(row) for row in rows]

@router.get("/api/research/{research_id}", response_model=ResearchResponse)
def detail(research_id: int, db: Session = Depends(get_db)) -> ResearchResponse:
    row = db.get(Research, research_id)
    if not row:
        raise HTTPException(404, "Research result not found")
    return to_response(row)

@router.delete("/api/research/{research_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(research_id: int, db: Session = Depends(get_db)) -> None:
    row = db.get(Research, research_id)
    if not row:
        raise HTTPException(404, "Research result not found")
    db.delete(row)
    db.commit()
