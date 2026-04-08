"""
test_customers.py — Unit tests for customer creation and deduplication.
"""

import pytest
from fastapi.testclient import TestClient


def test_add_customer_success(client: TestClient):
    """Create a new customer and get a customer_id."""
    resp = client.post(
        "/add_customer",
        json={"name": "Abebe Kebede", "phone": "0911111111"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "customer_id" in body
    assert body["customer_id"].isdigit()


def test_add_customer_duplicate_phone(client: TestClient):
    """Same phone number returns existing customer_id, not a new one."""
    phone = "0922222222"

    resp1 = client.post("/add_customer", json={"name": "Tigist Alemu", "phone": phone})
    assert resp1.status_code == 200
    id1 = resp1.json()["customer_id"]

    # Same phone, different name — should return same id
    resp2 = client.post("/add_customer", json={"name": "Different Name", "phone": phone})
    assert resp2.status_code == 200
    id2 = resp2.json()["customer_id"]

    assert id1 == id2


def test_add_customer_different_phones(client: TestClient):
    """Different phone numbers create different customer records."""
    resp1 = client.post("/add_customer", json={"name": "Customer A", "phone": "0933333333"})
    resp2 = client.post("/add_customer", json={"name": "Customer B", "phone": "0944444444"})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["customer_id"] != resp2.json()["customer_id"]


def test_add_customer_missing_name(client: TestClient):
    """name field is required."""
    resp = client.post("/add_customer", json={"phone": "0955555555"})
    assert resp.status_code == 422


def test_add_customer_missing_phone(client: TestClient):
    """phone field is required."""
    resp = client.post("/add_customer", json={"name": "No Phone"})
    assert resp.status_code == 422
