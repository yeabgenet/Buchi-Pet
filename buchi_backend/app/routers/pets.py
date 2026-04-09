from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import CreatePetResponse, GetPetsResponse, PetOut, PetDetailOut
from app.utils.file_handler import save_upload
from app.utils.the_dog_api import search_the_dog_api
from app.utils.petfinder_api import upload_image, list_uploaded_images, get_image_details, delete_image
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


@router.post("/upload_dog_image")
async def upload_dog_image(
    file: UploadFile = File(...),
    sub_id: Optional[str] = Form(None),
):
    """
    Upload a dog image to TheDogAPI.
    Accepts multipart/form-data with file and optional sub_id.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_data = await file.read()
    result = await upload_image(file_data, file.filename, sub_id)
    if not result:
        raise HTTPException(status_code=500, detail="Upload failed")

    return {"message": "Image uploaded successfully", "data": result}


@router.get("/list_uploaded_images")
async def list_user_uploaded_images(
    sub_id: Optional[str] = Query(None, description="Filter by sub_id"),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List uploaded dog images from TheDogAPI.
    Optionally filter by sub_id.
    """
    images = await list_uploaded_images(sub_id, limit)
    return {"images": images}


@router.get("/get_image/{image_id}")
async def get_dog_image_details(image_id: str):
    """
    Get details of a specific uploaded dog image by ID.
    """
    details = await get_image_details(image_id)
    if not details:
        raise HTTPException(status_code=404, detail="Image not found")

    return details


@router.delete("/delete_image/{image_id}")
async def delete_dog_image(image_id: str):
    """
    Delete an uploaded dog image by ID.
    """
    success = await delete_image(image_id)
    if not success:
        raise HTTPException(status_code=500, detail="Delete failed")

    return {"message": "Image deleted successfully"}

