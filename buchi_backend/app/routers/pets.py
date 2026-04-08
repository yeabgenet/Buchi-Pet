from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import CreatePetResponse, GetPetsResponse, PetOut, PetDetailOut
from app.utils.file_handler import save_upload
from app.utils.the_dog_api import search_the_dog_api
from app.models import PetPhoto

router = APIRouter(tags=["Pets"])


@router.post("/create_pet", response_model=CreatePetResponse)
async def create_pet(
    type: str = Form(...),
    gender: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    age: Optional[str] = Form(None),
    good_with_children: bool = Form(False),
    Photo: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    """
    Create a new pet with optional photos.
    Accepts multipart/form-data.

    - **type**: Dog | Cat | Bird | etc.
    - **gender**: male | female
    - **size**: small | medium | large | xlarge
    - **age**: baby | young | adult | senior
    - **good_with_children**: true | false
    - **Photo**: one or more image files
    """
    if not type or not type.strip():
        raise HTTPException(status_code=422, detail="type is required")

    # Create pet record first to get the ID
    pet_id = crud.create_pet(
        db=db,
        type=type.strip(),
        gender=gender.lower() if gender else None,
        size=size.lower() if size else None,
        age=age.lower() if age else None,
        good_with_children=good_with_children,
        photo_paths=[],
    )

    # Save uploaded photos and link to pet
    if Photo:
        for file in Photo:
            if file.filename:  # skip empty file slots
                file_path, url = await save_upload(file, pet_id)
                photo = PetPhoto(pet_id=pet_id, file_path=file_path, url=url)
                db.add(photo)
        db.commit()

    return CreatePetResponse(pet_id=str(pet_id))


@router.get("/get_pets", response_model=GetPetsResponse)
async def get_pets(
    type: Optional[List[str]] = Query(default=None, description="Dog, Cat — multiple allowed"),
    gender: Optional[List[str]] = Query(default=None, description="male, female — multiple allowed"),
    size: Optional[List[str]] = Query(default=None, description="small, medium, large, xlarge — multiple allowed"),
    age: Optional[List[str]] = Query(default=None, description="baby, young, adult, senior — multiple allowed"),
    good_with_children: Optional[bool] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Search pets from local DB. Supplements from TheDogAPI when local results < limit.
    Local results appear first.

    All filter params accept **multiple values**:
    `?type=Dog&type=Cat&age=baby&age=young`
    """
    # 1. Local results first
    local_pets = crud.search_pets(
        db=db,
        types=type,
        genders=gender,
        sizes=size,
        ages=age,
        good_with_children=good_with_children,
        limit=limit,
    )

    remaining = limit - len(local_pets)
    external_pets = []

    # 2. Supplement with TheDogAPI if needed
    if remaining > 0:
        # For external API, send just the first value of each filter
        ext_type = type[0] if type else None
        ext_gender = gender[0] if gender else None
        ext_size = size[0] if size else None
        ext_age = age[0] if age else None

        external_pets = await search_the_dog_api(
            type=ext_type,
            gender=ext_gender,
            size=ext_size,
            age=ext_age,
            good_with_children=good_with_children,
            limit=remaining,
        )
        external_pets = external_pets[:remaining]

    all_pets = local_pets + external_pets
    return GetPetsResponse(pets=[PetOut(**p) for p in all_pets])


@router.get("/get_pets/{pet_id}", response_model=PetDetailOut)
def get_pet_detail(
    pet_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve full details of a single local pet by ID.
    """
    pet = crud.get_pet_by_id(db=db, pet_id=pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet {pet_id} not found")
    return PetDetailOut(**pet)
