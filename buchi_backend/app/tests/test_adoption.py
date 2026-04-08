"""
test_adoption.py — Unit tests for adoption flow and report generation.
"""

import pytest
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────

def _create_pet(client: TestClient, type="Dog", gender="male", size="small", age="baby") -> str:
    resp = client.post(
        "/create_pet",
        data={"type": type, "gender": gender, "size": size, "age": age, "good_with_children": "true"},
    )
    assert resp.status_code == 200
    return resp.json()["pet_id"]


def _create_customer(client: TestClient, phone: str) -> str:
    resp = client.post("/add_customer", json={"name": "Test User", "phone": phone})
    assert resp.status_code == 200
    return resp.json()["customer_id"]


# ─────────────────────────────────────────────────────────
# POST /adopt
# ─────────────────────────────────────────────────────────

def test_adopt_success(client: TestClient):
    """Valid customer_id + pet_id creates an adoption request."""
    pet_id = _create_pet(client)
    customer_id = _create_customer(client, "0900000001")

    resp = client.post("/adopt", json={"customer_id": customer_id, "pet_id": pet_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "adoption_id" in body
    assert body["adoption_id"].isdigit()


def test_adopt_invalid_customer(client: TestClient):
    """Non-existent customer_id returns 404."""
    pet_id = _create_pet(client)
    resp = client.post("/adopt", json={"customer_id": "999999", "pet_id": pet_id})
    assert resp.status_code == 404


def test_adopt_invalid_pet(client: TestClient):
    """Non-existent pet_id returns 404."""
    customer_id = _create_customer(client, "0900000002")
    resp = client.post("/adopt", json={"customer_id": customer_id, "pet_id": "999999"})
    assert resp.status_code == 404


def test_adopt_non_numeric_ids(client: TestClient):
    """Non-numeric IDs return 422."""
    resp = client.post("/adopt", json={"customer_id": "abc", "pet_id": "xyz"})
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────
# POST /adopt_now  (combined flow)
# ─────────────────────────────────────────────────────────

def test_adopt_now_success(client: TestClient):
    """User enters name + phone + pet_id in one call."""
    pet_id = _create_pet(client, type="Cat")

    resp = client.post("/adopt_now", json={
        "name": "Yohannes Tesfaye",
        "phone": "0900000010",
        "pet_id": pet_id,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["adoption_id"].isdigit()


def test_adopt_now_duplicate_user(client: TestClient):
    """Same phone calling adopt_now twice → same customer, two adoption records."""
    pet_id1 = _create_pet(client, type="Dog")
    pet_id2 = _create_pet(client, type="Cat")

    resp1 = client.post("/adopt_now", json={"name": "Sara", "phone": "0900000020", "pet_id": pet_id1})
    resp2 = client.post("/adopt_now", json={"name": "Sara", "phone": "0900000020", "pet_id": pet_id2})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # Both adoptions created, different IDs
    assert resp1.json()["adoption_id"] != resp2.json()["adoption_id"]


def test_adopt_now_invalid_pet(client: TestClient):
    """adopt_now with non-existent pet_id returns 404."""
    resp = client.post("/adopt_now", json={
        "name": "Test", "phone": "0900000030", "pet_id": "999999",
    })
    assert resp.status_code == 404


# ─────────────────────────────────────────────────────────
# GET /get_adoption_requests
# ─────────────────────────────────────────────────────────

def test_get_adoption_requests_success(client: TestClient):
    """Returns adoption requests within date range."""
    resp = client.get("/get_adoption_requests?from_date=2020-01-01&to_date=2030-12-31")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert isinstance(body["data"], list)


def test_get_adoption_requests_fields(client: TestClient):
    """Each record contains required fields."""
    pet_id = _create_pet(client, type="Dog")
    client.post("/adopt_now", json={"name": "Field Test", "phone": "0900000040", "pet_id": pet_id})

    resp = client.get("/get_adoption_requests?from_date=2020-01-01&to_date=2030-12-31")
    assert resp.status_code == 200
    records = resp.json()["data"]
    assert len(records) > 0
    record = records[0]
    for field in ["customer_id", "customer_name", "customer_phone", "Pet_id", "type"]:
        assert field in record, f"Missing field: {field}"


def test_get_adoption_requests_bad_date(client: TestClient):
    """Invalid date format returns 422."""
    resp = client.get("/get_adoption_requests?from_date=01-01-2022&to_date=31-12-2022")
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────
# POST /generate_report
# ─────────────────────────────────────────────────────────

def test_generate_report_success(client: TestClient):
    """Report returns adopted_pet_types and weekly_adoption_requests."""
    resp = client.post("/generate_report", json={
        "from_date": "2020-01-01",
        "to_date": "2030-12-31",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "adopted_pet_types" in body["data"]
    assert "weekly_adoption_requests" in body["data"]


def test_generate_report_type_counts(client: TestClient):
    """Report counts reflect actual adoption data."""
    # Create and adopt a dog
    pet_id = _create_pet(client, type="Dog")
    client.post("/adopt_now", json={"name": "Report User", "phone": "0900000050", "pet_id": pet_id})

    resp = client.post("/generate_report", json={
        "from_date": "2020-01-01",
        "to_date": "2030-12-31",
    })
    assert resp.status_code == 200
    types = resp.json()["data"]["adopted_pet_types"]
    assert "Dog" in types
    assert types["Dog"] >= 1


# ─────────────────────────────────────────────────────────
# POST /pet_match
# ─────────────────────────────────────────────────────────

def test_pet_match_returns_results(client: TestClient):
    """pet_match returns scored pets matching preferences."""
    _create_pet(client, type="Dog", age="baby", size="small")

    resp = client.post("/pet_match", json={
        "type": "Dog",
        "age": "baby",
        "size": "small",
        "good_with_children": True,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert isinstance(body["pets"], list)


def test_pet_match_empty_no_matches(client: TestClient):
    """No pets matching highly specific criteria returns empty list gracefully."""
    resp = client.post("/pet_match", json={
        "type": "Dragon",
        "age": "senior",
    })
    assert resp.status_code == 200
    assert resp.json()["pets"] == []
