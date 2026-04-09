import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import get_engine, Base
from app.routers import pets, customers, adoption, reports, pet_match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup."""
    # logger.info("Creating database tables...")
    # engine = get_engine()
    # Base.metadata.create_all(bind=engine)
    # os.makedirs(settings.upload_dir, exist_ok=True)
    # logger.info(f"Upload directory ready: {settings.upload_dir}")
    yield
    logger.info("Shutting down Buchi backend...")


app = FastAPI(
    title="Buchi Pet Adoption API",
    description=(
        "Production-ready pet adoption backend with local DB storage, "
        "Petfinder API integration, and AI-style pet matching."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploaded pet photos) ──────────────────────────
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# ── Routers ─────────────────────────────────────────────────────
app.include_router(pets.router)
app.include_router(customers.router)
app.include_router(adoption.router)
app.include_router(reports.router)
app.include_router(pet_match.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "service": "Buchi Pet Adoption API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
