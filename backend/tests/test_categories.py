import pytest


def get_auth_token(client, email="cat_test@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Category User", "email": email, "password": "Password123!"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return res.json()["access_token"]


def test_default_categories_seeded_on_get(client):
    token = get_auth_token(client, "user_seed@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Request categories
    res = client.get("/api/v1/categories", headers=headers)
    assert res.status_code == 200
    categories = res.json()

    # Defaults: 10 expense + 6 income = 16 categories
    assert len(categories) == 16
    names = [c["name"] for c in categories]
    assert "Food" in names
    assert "Salary" in names
    assert "Travel" in names


def test_create_custom_category(client):
    token = get_auth_token(client, "user_custom_cat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"name": "Gym & Fitness", "type": "expense"}
    res = client.post("/api/v1/categories", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Gym & Fitness"
    assert data["type"] == "expense"
    assert data["id"] is not None


def test_create_duplicate_category_fails(client):
    token = get_auth_token(client, "user_duplicate_cat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"name": "Subscription", "type": "expense"}
    res1 = client.post("/api/v1/categories", json=payload, headers=headers)
    assert res1.status_code == 201

    # Attempt same name and type
    res2 = client.post("/api/v1/categories", json=payload, headers=headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_update_category(client):
    token = get_auth_token(client, "user_update_cat@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create category
    res = client.post("/api/v1/categories", json={"name": "Books", "type": "expense"}, headers=headers)
    cat_id = res.json()["id"]

    # Update name
    update_res = client.put(f"/api/v1/categories/{cat_id}", json={"name": "Books & Courses"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Books & Courses"


def test_category_user_isolation(client):
    token1 = get_auth_token(client, "cat_user1@example.com")
    token2 = get_auth_token(client, "cat_user2@example.com")

    # User 1 creates category
    res1 = client.post(
        "/api/v1/categories",
        json={"name": "Private Cat", "type": "expense"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    cat_id = res1.json()["id"]

    # User 2 attempts to edit User 1's category -> Should be 404
    res2 = client.put(
        f"/api/v1/categories/{cat_id}",
        json={"name": "Hacked Cat"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res2.status_code == 404

