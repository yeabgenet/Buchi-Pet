from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, time

from app.database import get_db
from app import crud
from app.schemas import ReportRequest, ReportResponse, ReportData

router = APIRouter(tags=["Reports"])


@router.post("/generate_report", response_model=ReportResponse)
def generate_report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a report for a date range:
    - Adopted pet type breakdown
    - Weekly adoption count buckets
    """
    from_dt = datetime.combine(payload.from_date, time.min)
    to_dt = datetime.combine(payload.to_date, time.max)

    if from_dt > to_dt:
        raise HTTPException(status_code=422, detail="from_date must be before to_date")

    report = crud.generate_report(db=db, from_date=from_dt, to_date=to_dt)

    return ReportResponse(
        data=ReportData(
            adopted_pet_types=report["adopted_pet_types"],
            weekly_adoption_requests=report["weekly_adoption_requests"],
        )
    )
