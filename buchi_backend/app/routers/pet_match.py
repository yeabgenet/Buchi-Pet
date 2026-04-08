from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import crud
from app.schemas import PetMatchRequest, PetMatchResponse, PetOut

router = APIRouter(tags=["Pet Match"])


@router.post("/pet_match", response_model=PetMatchResponse)
def pet_match(
    payload: PetMatchRequest,
    db: Session = Depends(get_db),
):
    """
    AI-style pet recommendation engine.

    Scores local pets based on matching criteria:
      - type match   → +5 pts
      - age match    → +3 pts
      - size match   → +2 pts
      - children     → +4 pts
      - breed match  → +2 pts

    Returns top scored pets.
    """
    matches = crud.pet_match(
        db=db,
        type=payload.type,
        age=payload.age,
        size=payload.size,
        good_with_children=payload.good_with_children,
        breed=payload.breed,
    )
    return PetMatchResponse(pets=[PetOut(**p) for p in matches])
