"""
test_pets.py — Unit tests for pet creation, search, and detail endpoints.
"""

import io
import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────
# POST /create_pet
# ─────────────────────────────────────────────────────────

def test_create_pet_minimal(client: TestClient):
    """Create pet with only required field (type)."""
    resp = client.post("/create_pet", data={"type": "Dog"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "pet_id" in body
    assert body["pet_id"].isdigit()


def test_create_pet_full(client: TestClient):
    """Create pet with all fields."""
    resp = client.post(
        "/create_pet",
        data={
            "type": "Cat",
            "gender": "female",
            "size": "small",
            "age": "baby",
            "good_with_children": "true",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["pet_id"].isdigit()


def test_create_pet_with_photo(client: TestClient):
    """Create pet with an in-memory JPEG upload."""
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # minimal JPEG header
    fake_image.name = "dog.jpg"

    resp = client.post(
        "/create_pet",
        data={"type": "Dog", "gender": "male", "size": "medium", "age": "adult"},
        files=[("Photo", ("dog.jpg", fake_image, "image/jpeg"))],
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_create_pet_missing_type(client: TestClient):
    """type is required — should fail."""
    resp = client.post("/create_pet", data={"gender": "male"})
    assert resp.status_code == 422


def test_create_pet_xlarge_size(client: TestClient):
    """xlarge is a valid size value."""
    resp = client.post(
        "/create_pet",
        data={"type": "Dog", "size": "xlarge", "age": "adult"},
    )
    assert resp.status_code == 200


# ─────────────────────────────────────────────────────────
# GET /get_pets
# ─────────────────────────────────────────────────────────

def test_get_pets_no_filters(client: TestClient):
    """Return pets with default limit."""
    resp = client.get("/get_pets?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "pets" in body
    assert len(body["pets"]) <= 5


def test_get_pets_filter_by_type(client: TestClient):
    """Filter pets by type=Dog."""
    # Create a Dog first
    client.post("/create_pet", data={"type": "Dog", "size": "small"})

    resp = client.get("/get_pets?type=Dog&limit=10")
    assert resp.status_code == 200
    pets = resp.json()["pets"]
    local_pets = [p for p in pets if p["source"] == "local"]
    for p in local_pets:
        assert p["type"].lower() == "dog"


def test_get_pets_multi_type(client: TestClient):
    """Multi-select: type=Dog&type=Cat should return both."""
    client.post("/create_pet", data={"type": "Dog"})
    client.post("/create_pet", data={"type": "Cat"})

    resp = client.get("/get_pets?type=Dog&type=Cat&limit=20")
    assert resp.status_code == 200
    pets = resp.json()["pets"]
    local_pets = [p for p in pets if p["source"] == "local"]
    types_found = {p["type"].lower() for p in local_pets}
    assert "dog" in types_found
    assert "cat" in types_found


def test_get_pets_multi_age(client: TestClient):
    """age=baby&age=young returns both age groups."""
    client.post("/create_pet", data={"type": "Dog", "age": "baby"})
    client.post("/create_pet", data={"type": "Dog", "age": "young"})

    resp = client.get("/get_pets?age=baby&age=young&limit=20")
    assert resp.status_code == 200
    pets = resp.json()["pets"]
    local_pets = [p for p in pets if p["source"] == "local"]
    ages_found = {p["age"] for p in local_pets if p["age"]}
    assert "baby" in ages_found
    assert "young" in ages_found


def test_get_pets_multi_size(client: TestClient):
    """size=small&size=medium returns both."""
    client.post("/create_pet", data={"type": "Cat", "size": "small"})
    client.post("/create_pet", data={"type": "Cat", "size": "medium"})

    resp = client.get("/get_pets?size=small&size=medium&limit=20")
    assert resp.status_code == 200
    pets = resp.json()["pets"]
    local_pets = [p for p in pets if p["source"] == "local"]
    sizes_found = {p["size"] for p in local_pets if p["size"]}
    assert "small" in sizes_found
    assert "medium" in sizes_found


def test_get_pets_good_with_children(client: TestClient):
    """Filter by good_with_children=true."""
    client.post("/create_pet", data={"type": "Dog", "good_with_children": "true"})

    resp = client.get("/get_pets?good_with_children=true&limit=10")
    assert resp.status_code == 200
    pets = resp.json()["pets"]
    local_pets = [p for p in pets if p["source"] == "local"]
    for p in local_pets:
        assert p["good_with_children"] is True


def test_get_pets_limit_enforced(client: TestClient):
    """Limit parameter is enforced."""
    resp = client.get("/get_pets?limit=2")
    assert resp.status_code == 200
    assert len(resp.json()["pets"]) <= 2


def test_get_pets_invalid_limit(client: TestClient):
    """limit=0 should be rejected."""
    resp = client.get("/get_pets?limit=0")
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────
# GET /get_pets/{pet_id}
# ─────────────────────────────────────────────────────────

def test_get_pet_detail(client: TestClient):
    """Get full detail of an existing pet."""
    create = client.post(
        "/create_pet",
        data={"type": "Dog", "gender": "male", "size": "large", "age": "adult"},
    )
    pet_id = create.json()["pet_id"]

    resp = client.get(f"/get_pets/{pet_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pet_id"] == pet_id
    assert body["type"].lower() == "dog"
    assert body["gender"] == "male"
    assert body["size"] == "large"
    assert body["age"] == "adult"


def test_get_pet_detail_not_found(client: TestClient):
    """Non-existent pet_id returns 404."""
    resp = client.get("/get_pets/999999999")
    assert resp.status_code == 404
