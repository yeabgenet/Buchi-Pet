import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum, ForeignKey,
    DateTime, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


class AdoptionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class PetSource(str, enum.Enum):
    local = "local"
    petfinder = "petfinder"


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # Dog, Cat, etc.

    breeds = relationship("Breed", back_populates="species")
    pets = relationship("Pet", back_populates="species")


class Breed(Base):
    __tablename__ = "breeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)

    species = relationship("Species", back_populates="breeds")
    pets = relationship("Pet", back_populates="breed")


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(String(50), nullable=False)        # Dog / Cat / etc.
    gender = Column(String(20), nullable=True)       # male / female
    size = Column(String(20), nullable=True)         # small / medium / large
    age = Column(String(20), nullable=True)          # baby / young / adult / senior
    good_with_children = Column(Boolean, default=False)
    source = Column(Enum(PetSource), default=PetSource.local, nullable=False)
    external_id = Column(String(100), nullable=True, index=True)

    species_id = Column(Integer, ForeignKey("species.id"), nullable=True)
    breed_id = Column(Integer, ForeignKey("breeds.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    species = relationship("Species", back_populates="pets")
    breed = relationship("Breed", back_populates="pets")
    photos = relationship("PetPhoto", back_populates="pet", cascade="all, delete-orphan")
    adoption_requests = relationship("AdoptionRequest", back_populates="pet")


class PetPhoto(Base):
    __tablename__ = "pet_photos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)

    pet = relationship("Pet", back_populates="photos")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(30), unique=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    adoption_requests = relationship("AdoptionRequest", back_populates="customer")


class AdoptionRequest(Base):
    __tablename__ = "adoption_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    status = Column(Enum(AdoptionStatus), default=AdoptionStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="adoption_requests")
    pet = relationship("Pet", back_populates="adoption_requests")
