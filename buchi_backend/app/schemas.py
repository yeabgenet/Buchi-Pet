from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date


# ─────────────────────────────────────────────
# Pet Schemas
# ─────────────────────────────────────────────

class CreatePetRequest(BaseModel):
    type: str
    gender: Optional[str] = None
    size: Optional[str] = None
    age: Optional[str] = None
    good_with_children: Optional[bool] = False

    @field_validator("type")
    @classmethod
    def type_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("type must not be empty")
        return v.strip()


class CreatePetResponse(BaseModel):
    status: str = "success"
    pet_id: str


class PetOut(BaseModel):
    pet_id: str
    source: str
    type: str
    gender: Optional[str] = None
    size: Optional[str] = None
    age: Optional[str] = None
    good_with_children: Optional[bool] = None
    Photos: List[str] = []


class PetDetailOut(BaseModel):
    pet_id: str
    source: str
    type: str
    gender: Optional[str] = None
    size: Optional[str] = None
    age: Optional[str] = None
    good_with_children: Optional[bool] = None
    Photos: List[str] = []
    breed: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class GetPetsResponse(BaseModel):
    status: str = "success"
    pets: List[PetOut]


# ─────────────────────────────────────────────
# Customer Schemas
# ─────────────────────────────────────────────

class AddCustomerRequest(BaseModel):
    name: str
    phone: str


class AddCustomerResponse(BaseModel):
    status: str = "success"
    customer_id: str


# ─────────────────────────────────────────────
# Adoption Schemas
# ─────────────────────────────────────────────

class AdoptRequest(BaseModel):
    customer_id: str
    pet_id: str


class AdoptWithDetailsRequest(BaseModel):
    """Combined adopt endpoint — user enters name+phone+pet_id in one shot."""
    name: str
    phone: str
    pet_id: str


class AdoptResponse(BaseModel):
    status: str = "success"
    adoption_id: str


class AdoptionRecordOut(BaseModel):
    customer_id: str
    customer_phone: str
    customer_name: str
    Pet_id: str
    type: str
    gender: Optional[str] = None
    size: Optional[str] = None
    age: Optional[str] = None
    good_with_children: Optional[bool] = None


class GetAdoptionRequestsRequest(BaseModel):
    from_date: date
    to_date: date


class GetAdoptionRequestsResponse(BaseModel):
    status: str = "success"
    data: List[AdoptionRecordOut]


# ─────────────────────────────────────────────
# Report Schemas
# ─────────────────────────────────────────────

class ReportRequest(BaseModel):
    from_date: date
    to_date: date


class ReportData(BaseModel):
    adopted_pet_types: dict
    weekly_adoption_requests: dict


class ReportResponse(BaseModel):
    status: str = "success"
    data: ReportData


# ─────────────────────────────────────────────
# Pet Match Schemas
# ─────────────────────────────────────────────

class PetMatchRequest(BaseModel):
    type: Optional[str] = None
    age: Optional[str] = None
    size: Optional[str] = None
    good_with_children: Optional[bool] = None
    breed: Optional[str] = None


class PetMatchResponse(BaseModel):
    status: str = "success"
    pets: List[PetOut]
