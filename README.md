# 🐾 Buchi Pet Adoption API

A production-ready **FastAPI** backend for a pet adoption platform.



## Tech Stack

- Python 3.11+
- FastAPI framework
- SQLAlchemy ORM + Pydantic schemas
- PostgreSQL 15 database
- Docker Compose for local deployment
- HTTPX for async external API calls
- Local image uploads served from `uploads/`

## Features

- 📦 **PostgreSQL 15** database with 6 normalized tables
- 🐕 **TheDogAPI** integration for external dog search
- 📸 **Photo upload** stored locally and served via URL
- 🤖 **Pet matching** engine with weighted scoring
- 📊 **Analytics reports** with weekly adoption breakdowns
- 🐳 **Docker Compose** — single command deployment

---

## Quick Start

```bash
# Clone and navigate to the project
cd buchi_backend

# Run with Docker
docker-compose up

# Rebuild after changes
docker-compose up --build
```

**API available at:** http://localhost:8000  
**Swagger docs:** http://localhost:8000/docs  
**Health check:** http://localhost:8000/health

**Requirements:**
- Docker Desktop installed
- No local PostgreSQL needed (runs in Docker container)

---

## Third-party API Endpoints

- TheDogAPI search: `https://api.thedogapi.com/v1/images/search`
- TheDogAPI upload image: `https://api.thedogapi.com/v1/images/upload`
- TheDogAPI list images: `https://api.thedogapi.com/v1/images`
- TheDogAPI image details / delete: `https://api.thedogapi.com/v1/images/{image_id}`

This project uses TheDogAPI as an external data source for pet search fallback and image uploads.

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/create_pet` | Create a pet with photos (multipart form) |
| `GET` | `/get_pets` | Search pets (local DB + TheDogAPI fallback) |
| `POST` | `/add_customer` | Register a customer (deduplicates by phone) |
| `POST` | `/adopt` | Submit an adoption request |
| `GET` | `/get_adoption_requests` | List adoption requests by date range |
| `POST` | `/generate_report` | Analytics report for a date range |
| `POST` | `/pet_match` | AI-style pet matching by preferences |

---

## Example Requests

### Create a Pet
```bash
curl -X POST http://localhost:8000/create_pet \
  -F "type=Dog" \
  -F "gender=male" \
  -F "size=small" \
  -F "age=baby" \
  -F "good_with_children=true" \
  -F "Photo=@/path/to/photo.jpg"
```

### Search Pets
```bash
curl "http://localhost:8000/get_pets?type=Dog&size=small&limit=5"
```

### Add Customer
```bash
curl -X POST http://localhost:8000/add_customer \
  -H "Content-Type: application/json" \
  -d '{"name": "Abebe Kebede", "phone": "0922222222"}'
```

### Adopt a Pet
```bash
curl -X POST http://localhost:8000/adopt \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "1", "pet_id": "1"}'
```

### Pet Match
```bash
curl -X POST http://localhost:8000/pet_match \
  -H "Content-Type: application/json" \
  -d '{"type": "Dog", "age": "baby", "size": "small", "good_with_children": true}'
```

---

## Project Structure

```
app/
├── main.py            # FastAPI app, CORS, static files, router registration
├── config.py          # Settings from environment
├── database.py        # SQLAlchemy engine + session
├── models.py          # ORM: Species, Breed, Pet, PetPhoto, Customer, AdoptionRequest
├── schemas.py         # Pydantic request/response schemas
├── crud.py            # All business logic
├── utils/
│   ├── file_handler.py    # Async photo upload
│   └── the_dog_api.py     # TheDogAPI client
└── routers/
    ├── pets.py
    ├── customers.py
    ├── adoption.py
    ├── reports.py
    └── pet_match.py
```

---

## Testing

Run the unit tests with pytest:

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest app/tests/ -v

# Run with coverage
python -m pytest app/tests/ --cov=app --cov-report=html
```

**Test Coverage:**
- Pet creation, search (multi-select filters), and details
- Customer registration and deduplication
- Adoption flows (by IDs and combined flow)
- Reports and analytics
- Pet matching engine

---

## API Documentation

Import the Postman collection from `Buchi_Pet_API.postman_collection.json`


## Production Deployment

The app supports multiple production server configurations:

1. **Gunicorn** (recommended): `gunicorn app.main:app --config gunicorn.conf.py`
2. **uWSGI**: `uwsgi --ini uwsgi.ini`
3. **Docker**:` docker-compose up` or `docker-compose up --build`
