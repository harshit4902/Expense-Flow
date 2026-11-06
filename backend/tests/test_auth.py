import pytest
from app.services.auth_service import get_password_hash, verify_password


def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = get_password_hash(password)

    # Must be hashed and not plain text
    assert hashed != password
    assert hashed.startswith("$argon2id$")

    # Verification must succeed for correct password
    assert verify_password(password, hashed) is True

    # Verification must fail for wrong password
    assert verify_password("WrongPassword123!", hashed) is False


def test_user_registration_success(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["name"] == "Jane Doe"
    assert "hashed_password" not in data["user"]


def test_user_registration_duplicate_email(client):
    payload = {
        "name": "Jane Duplicate",
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    # First registration
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email should fail
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_user_registration_validation(client):
    # Short password and invalid email
    payload = {
        "name": "J",
        "email": "not-an-email",
        "password": "123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_user_login_success(client):
    # Register first
    reg_payload = {
        "name": "John Login",
        "email": "johnlogin@example.com",
        "password": "CorrectPassword!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "johnlogin@example.com",
        "password": "CorrectPassword!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "johnlogin@example.com"


def test_user_login_invalid_password(client):
    reg_payload = {
        "name": "John Wrong",
        "email": "johnwrong@example.com",
        "password": "CorrectPassword!",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "johnwrong@example.com",
        "password": "IncorrectPassword!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_user_login_nonexistent_email(client):
    login_payload = {
        "email": "doesnotexist@example.com",
        "password": "AnyPassword!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401


def test_get_current_user_me(client):
    reg_payload = {
        "name": "Current User Test",
        "email": "currentuser@example.com",
        "password": "Password123!",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    # Call /auth/me with valid Bearer token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "currentuser@example.com"
    assert data["name"] == "Current User Test"


def test_get_current_user_unauthorized(client):
    # Call without token
    response1 = client.get("/api/v1/auth/me")
    assert response1.status_code == 401

    # Call with forged/invalid token
    response2 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response2.status_code == 401

