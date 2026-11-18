import uuid


def test_register_and_login(client):
    email = f"user_{uuid.uuid4().hex[:8]}@test.com"

    r = client.post("/auth/register", json={
        "full_name": "Test User",
        "email": email,
        "password": "Test@12345",
    })
    assert r.status_code == 201
    assert r.json()["role"] == "customer"

    r = client.post("/auth/login", json={"email": email, "password": "Test@12345"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_duplicate_email(client):
    email = f"user_{uuid.uuid4().hex[:8]}@test.com"
    data = {"full_name": "Test User", "email": email, "password": "Test@12345"}

    assert client.post("/auth/register", json=data).status_code == 201
    assert client.post("/auth/register", json=data).status_code == 400


def test_wrong_password(client):
    email = f"user_{uuid.uuid4().hex[:8]}@test.com"
    client.post("/auth/register", json={
        "full_name": "Test User", "email": email, "password": "Test@12345"
    })

    r = client.post("/auth/login", json={"email": email, "password": "Wrong@12345"})
    assert r.status_code == 401


def test_cannot_register_as_admin(client):
    r = client.post("/auth/register", json={
        "full_name": "Hacker",
        "email": f"hack_{uuid.uuid4().hex[:8]}@test.com",
        "password": "Test@12345",
        "role": "admin",
    })
    assert r.status_code == 422


def test_me_needs_token(client):
    assert client.get("/auth/me").status_code in (401, 403)