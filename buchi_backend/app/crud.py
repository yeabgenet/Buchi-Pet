"""
crud.py — All database business logic.
Routers call these functions; they never touch the DB directly.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException

from app import models


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _get_or_create_species(db: Session, name: str) -> models.Species:
    species = db.query(models.Species).filter(
        func.lower(models.Species.name) == name.lower()
    ).first()
    if not species:
        species = models.Species(name=name.capitalize())
        db.add(species)
        db.flush()
    return species


def _pet_to_dict(pet: models.Pet) -> dict:
    return {
        "pet_id": str(pet.id),
        "source": pet.source.value if pet.source else "local",
        "type": pet.type,
        "gender": pet.gender,
        "size": pet.size,
        "age": pet.age,
        "good_with_children": pet.good_with_children,
        "Photos": [p.url for p in pet.photos],
    }


def _pet_to_detail_dict(pet: models.Pet) -> dict:
    d = _pet_to_dict(pet)
    d["breed"] = pet.breed.name if pet.breed else None
    d["created_at"] = pet.created_at.isoformat() if pet.created_at else None
    return d


# ─────────────────────────────────────────────────────────────
# Pet CRUD
# ─────────────────────────────────────────────────────────────

def create_pet(
    db: Session,
    type: str,
    gender: Optional[str],
    size: Optional[str],
    age: Optional[str],
    good_with_children: bool,
    photo_paths: List[tuple],  # list of (file_path, public_url)
) -> int:
    """Insert a pet and its photos. Returns pet_id."""

    species = _get_or_create_species(db, type)

    pet = models.Pet(
        type=type.capitalize(),
        gender=gender,
        size=size,
        age=age,
        good_with_children=good_with_children,
        source=models.PetSource.local,
        species_id=species.id,
    )
    db.add(pet)
    db.flush()  # get pet.id before inserting photos

    for file_path, url in photo_paths:
        photo = models.PetPhoto(pet_id=pet.id, file_path=file_path, url=url)
        db.add(photo)

    db.commit()
    db.refresh(pet)
    return pet.id


def get_pet_by_id(db: Session, pet_id: int) -> Optional[dict]:
    """Return a single pet's full details, or None if not found."""
    pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
    if not pet:
        return None
    return _pet_to_detail_dict(pet)


def search_pets(
    db: Session,
    types: Optional[List[str]] = None,
    genders: Optional[List[str]] = None,
    sizes: Optional[List[str]] = None,
    ages: Optional[List[str]] = None,
    good_with_children: Optional[bool] = None,
    limit: int = 10,
) -> List[dict]:
    """
    Query local DB pets with optional multi-value filters.
    All list filters use SQL IN — passing multiple values = OR logic.
    """

    query = db.query(models.Pet).filter(
        models.Pet.source == models.PetSource.local
    )

    if types:
        normalized = [t.lower() for t in types]
        query = query.filter(func.lower(models.Pet.type).in_(normalized))
    if genders:
        normalized = [g.lower() for g in genders]
        query = query.filter(func.lower(models.Pet.gender).in_(normalized))
    if sizes:
        normalized = [s.lower() for s in sizes]
        query = query.filter(func.lower(models.Pet.size).in_(normalized))
    if ages:
        normalized = [a.lower() for a in ages]
        query = query.filter(func.lower(models.Pet.age).in_(normalized))
    if good_with_children is not None:
        query = query.filter(models.Pet.good_with_children == good_with_children)

    pets = query.order_by(models.Pet.created_at.desc()).limit(limit).all()
    return [_pet_to_dict(p) for p in pets]


# ─────────────────────────────────────────────────────────────
# Customer CRUD
# ─────────────────────────────────────────────────────────────

def add_customer(db: Session, name: str, phone: str) -> int:
    """Create a new customer or return existing id if phone exists."""

    existing = db.query(models.Customer).filter(
        models.Customer.phone == phone
    ).first()

    if existing:
        return existing.id

    customer = models.Customer(name=name, phone=phone)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer.id


def get_customer_by_id(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


# ─────────────────────────────────────────────────────────────
# Adoption CRUD
# ─────────────────────────────────────────────────────────────

def create_adoption(db: Session, customer_id: int, pet_id: int) -> int:
    """Create an adoption request. Validates customer + pet existence."""

    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    pet = db.query(models.Pet).filter(models.Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail=f"Pet {pet_id} not found")

    adoption = models.AdoptionRequest(
        customer_id=customer_id,
        pet_id=pet_id,
        status=models.AdoptionStatus.pending,
    )
    db.add(adoption)
    db.commit()
    db.refresh(adoption)
    return adoption.id


def get_adoption_requests(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> List[dict]:
    """Return adoption requests in date range, oldest first."""

    requests = (
        db.query(models.AdoptionRequest)
        .filter(
            and_(
                models.AdoptionRequest.created_at >= from_date,
                models.AdoptionRequest.created_at <= to_date,
            )
        )
        .order_by(models.AdoptionRequest.created_at.asc())
        .all()
    )

    results = []
    for req in requests:
        results.append({
            "customer_id": str(req.customer_id),
            "customer_phone": req.customer.phone,
            "customer_name": req.customer.name,
            "Pet_id": str(req.pet_id),
            "type": req.pet.type,
            "gender": req.pet.gender,
            "size": req.pet.size,
            "age": req.pet.age,
            "good_with_children": req.pet.good_with_children,
        })
    return results


# ─────────────────────────────────────────────────────────────
# Report CRUD
# ─────────────────────────────────────────────────────────────

def generate_report(
    db: Session,
    from_date: datetime,
    to_date: datetime,
) -> dict:
    """Generate adoption report: pet type counts + weekly breakdown."""

    requests = (
        db.query(models.AdoptionRequest)
        .filter(
            and_(
                models.AdoptionRequest.created_at >= from_date,
                models.AdoptionRequest.created_at <= to_date,
            )
        )
        .all()
    )

    # Pet type breakdown
    type_counts: dict = {}
    for req in requests:
        pet_type = req.pet.type if req.pet else "Unknown"
        type_counts[pet_type] = type_counts.get(pet_type, 0) + 1

    # Weekly buckets (7-day windows starting from from_date)
    weekly: dict = {}
    current = from_date
    while current <= to_date:
        week_key = current.strftime("%Y-%m-%d")
        week_end = current + timedelta(days=7)
        count = sum(
            1 for r in requests
            if current <= r.created_at < week_end
        )
        weekly[week_key] = count
        current = week_end

    return {
        "adopted_pet_types": type_counts,
        "weekly_adoption_requests": weekly,
    }


# ─────────────────────────────────────────────────────────────
# Pet Match CRUD
# ─────────────────────────────────────────────────────────────

def pet_match(
    db: Session,
    type: Optional[str] = None,
    age: Optional[str] = None,
    size: Optional[str] = None,
    good_with_children: Optional[bool] = None,
    breed: Optional[str] = None,
    limit: int = 10,
) -> List[dict]:
    """
    Score and rank local pets by how well they match user preferences.

    Scoring weights:
      type match          → +5 pts
      good_with_children  → +4 pts
      age match           → +3 pts
      size match          → +2 pts
      breed match         → +2 pts
    """

    pets = db.query(models.Pet).filter(
        models.Pet.source == models.PetSource.local
    ).all()

    scored = []
    for pet in pets:
        score = 0
        if type and pet.type and pet.type.lower() == type.lower():
            score += 5
        if age and pet.age and pet.age.lower() == age.lower():
            score += 3
        if size and pet.size and pet.size.lower() == size.lower():
            score += 2
        if good_with_children is not None and pet.good_with_children == good_with_children:
            score += 4
        if breed and pet.breed and pet.breed.name.lower() == breed.lower():
            score += 2

        if score > 0:
            scored.append((score, pet))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [_pet_to_dict(p) for _, p in scored[:limit]]
