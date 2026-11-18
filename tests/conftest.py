import random
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


def random_phone():
    return str(random.randint(6, 9)) + "".join(str(random.randint(0, 9)) for _ in range(9))


def random_pincode():
    return str(random.randint(100000, 999999))


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def register_and_login(client, role):
    email = f"{role}_{uuid.uuid4().hex[:8]}@test.com"
    password = "Test@12345"

    r = client.post("/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "password": password,
        "role": role,
    })
    assert r.status_code == 201

    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200

    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture
def make_customer(client):
    def _make(pincode=None):
        headers = register_and_login(client, "customer")
        r = client.post("/customers/profile", headers=headers, json={
            "phone": random_phone(),
            "address": "Test address, Pune",
            "city": "Pune",
            "pincode": pincode or random_pincode(),
        })
        assert r.status_code == 201
        return headers
    return _make


@pytest.fixture
def make_partner(client):
    def _make(pincode=None):
        headers = register_and_login(client, "delivery_partner")
        r = client.post("/partners/profile", headers=headers, json={
            "phone": random_phone(),
            "vehicle_type": "Bike",
            "vehicle_number": "MH12" + uuid.uuid4().hex[:6].upper(),
            "city": "Pune",
            "pincode": pincode or random_pincode(),
        })
        assert r.status_code == 201
        return headers
    return _make


@pytest.fixture
def admin_headers(client):
    r = client.post("/auth/login", json={
        "email": "admin@loadshare.com",
        "password": "Admin@12345",
    })
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture
def order_payload():
    def _payload(pincode):
        return {
            "pickup_address": "Pickup address, Pune",
            "pickup_pincode": pincode,
            "delivery_address": "Delivery address, Pune",
            "delivery_pincode": pincode,
            "package_description": "Books",
            "weight_kg": 2,
        }
    return _payload