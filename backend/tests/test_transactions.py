import datetime
import pytest


def get_user_and_categories(client, email="tx_user@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Transaction User", "email": email, "password": "Password123!"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch default categories
    cats = client.get("/api/v1/categories", headers=headers).json()
    food_cat = next(c for c in cats if c["name"] == "Food")
    salary_cat = next(c for c in cats if c["name"] == "Salary")
    return headers, food_cat["id"], salary_cat["id"]


def test_create_expense_and_income_transactions(client):
    headers, food_id, salary_id = get_user_and_categories(client, "tx_create@example.com")

    # 1. Create Expense: ₹250.50 (25050 paise)
    expense_payload = {
        "category_id": food_id,
        "amount": 25050,
        "type": "expense",
        "description": "Lunch at restaurant",
        "transaction_date": "2026-11-02",
    }
    res = client.post("/api/v1/transactions", json=expense_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["amount"] == 25050
    assert data["amount_in_rupees"] == 250.50
    assert data["type"] == "expense"
    assert data["description"] == "Lunch at restaurant"
    assert data["category"]["name"] == "Food"

    # 2. Create Income: ₹50,000.00 (5000000 paise)
    income_payload = {
        "category_id": salary_id,
        "amount": 5000000,
        "type": "income",
        "description": "Monthly Salary",
        "transaction_date": "2026-11-01",
    }
    res2 = client.post("/api/v1/transactions", json=income_payload, headers=headers)
    assert res2.status_code == 201
    assert res2.json()["amount"] == 5000000
    assert res2.json()["amount_in_rupees"] == 50000.00


def test_transaction_type_mismatch_fails(client):
    headers, food_id, _ = get_user_and_categories(client, "tx_mismatch@example.com")

    # Food is expense, attempting to record as 'income' must fail
    invalid_payload = {
        "category_id": food_id,
        "amount": 10000,
        "type": "income",
        "description": "Invalid income for food",
        "transaction_date": "2026-11-02",
    }
    res = client.post("/api/v1/transactions", json=invalid_payload, headers=headers)
    assert res.status_code == 400
    assert "is of type 'expense'" in res.json()["detail"]


def test_transaction_filtering_and_search(client):
    headers, food_id, salary_id = get_user_and_categories(client, "tx_filter@example.com")

    # Add 3 transactions
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": food_id,
            "amount": 15000,
            "type": "expense",
            "description": "Office Coffee",
            "transaction_date": "2026-11-01",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": food_id,
            "amount": 45000,
            "type": "expense",
            "description": "Dinner with friends",
            "transaction_date": "2026-11-02",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": salary_id,
            "amount": 7500000,
            "type": "income",
            "description": "Salary credited",
            "transaction_date": "2026-11-01",
        },
        headers=headers,
    )

    # Filter by type=income
    res_inc = client.get("/api/v1/transactions?type=income", headers=headers)
    assert res_inc.status_code == 200
    assert res_inc.json()["total"] == 1
    assert res_inc.json()["items"][0]["description"] == "Salary credited"

    # Search by keyword "Coffee"
    res_search = client.get("/api/v1/transactions?search=Coffee", headers=headers)
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["description"] == "Office Coffee"

    # Filter by date range
    res_date = client.get(
        "/api/v1/transactions?start_date=2026-11-02&end_date=2026-11-02",
        headers=headers,
    )
    assert res_date.status_code == 200
    assert res_date.json()["total"] == 1
    assert res_date.json()["items"][0]["description"] == "Dinner with friends"


def test_transaction_update_and_delete(client):
    headers, food_id, _ = get_user_and_categories(client, "tx_crud@example.com")

    # Create
    create_res = client.post(
        "/api/v1/transactions",
        json={
            "category_id": food_id,
            "amount": 20000,
            "type": "expense",
            "description": "Snacks",
            "transaction_date": "2026-11-02",
        },
        headers=headers,
    )
    tx_id = create_res.json()["id"]

    # Update description and amount
    update_res = client.put(
        f"/api/v1/transactions/{tx_id}",
        json={"amount": 25000, "description": "Snacks and Drinks"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["amount"] == 25000
    assert update_res.json()["description"] == "Snacks and Drinks"

    # Delete
    del_res = client.delete(f"/api/v1/transactions/{tx_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify not found
    get_res = client.get(f"/api/v1/transactions/{tx_id}", headers=headers)
    assert get_res.status_code == 404


def test_transaction_user_isolation(client):
    headers1, food1_id, _ = get_user_and_categories(client, "iso_user1@example.com")
    headers2, _, _ = get_user_and_categories(client, "iso_user2@example.com")

    # User 1 creates a transaction
    tx_res = client.post(
        "/api/v1/transactions",
        json={
            "category_id": food1_id,
            "amount": 10000,
            "type": "expense",
            "description": "User 1 secret expense",
            "transaction_date": "2026-11-02",
        },
        headers=headers1,
    )
    tx_id = tx_res.json()["id"]

    # User 2 tries to read User 1's transaction -> Must return 404
    res_read = client.get(f"/api/v1/transactions/{tx_id}", headers=headers2)
    assert res_read.status_code == 404

    # User 2 tries to delete User 1's transaction -> Must return 404
    res_del = client.delete(f"/api/v1/transactions/{tx_id}", headers=headers2)
    assert res_del.status_code == 404

