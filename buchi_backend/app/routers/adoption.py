from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import AdoptRequest, AdoptResponse, AdoptWithDetailsRequest

router = APIRouter(tags=["Adoption"])


@router.post("/adopt", response_model=AdoptResponse)
def adopt(
    payload: AdoptRequest,
    db: Session = Depends(get_db),
):
    """
    Submit an adoption request using existing customer_id and pet_id.
    Returns 404 if either does not exist.
    """
    try:
        customer_id = int(payload.customer_id)
        pet_id = int(payload.pet_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="customer_id and pet_id must be numeric")

    adoption_id = crud.create_adoption(db=db, customer_id=customer_id, pet_id=pet_id)
    return AdoptResponse(adoption_id=str(adoption_id))


@router.post("/adopt_now", response_model=AdoptResponse)
def adopt_now(
    payload: AdoptWithDetailsRequest,
    db: Session = Depends(get_db),
):
    """
    Combined adopt endpoint — user presses ADOPT, enters name + phone + pet_id.
    Automatically creates/finds customer then creates adoption request.

    This is the primary mobile/web flow:
    1. User taps Adopt on a pet
    2. App collects name + phone
    3. Single call to this endpoint — no pre-registration needed
    """
    try:
        pet_id = int(payload.pet_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="pet_id must be numeric")

    # Upsert customer (deduplicates by phone)
    customer_id = crud.add_customer(
        db=db,
        name=payload.name.strip(),
        phone=payload.phone.strip(),
    )

    # Create adoption request
    adoption_id = crud.create_adoption(db=db, customer_id=customer_id, pet_id=pet_id)
    return AdoptResponse(adoption_id=str(adoption_id))


@router.get("/get_adoption_requests", response_model=dict)
def get_adoption_requests(
    from_date: str,
    to_date: str,
    db: Session = Depends(get_db),
):
    """
    Fetch all adoption requests within a date range (YYYY-MM-DD).
    Ordered ascending — oldest requests appear first.
    """
    from datetime import datetime, time

    try:
        from_dt = datetime.combine(datetime.strptime(from_date, "%Y-%m-%d").date(), time.min)
        to_dt = datetime.combine(datetime.strptime(to_date, "%Y-%m-%d").date(), time.max)
    except ValueError:
        raise HTTPException(status_code=422, detail="Dates must be in YYYY-MM-DD format")

    records = crud.get_adoption_requests(db=db, from_date=from_dt, to_date=to_dt)
    return {"status": "success", "data": records}
