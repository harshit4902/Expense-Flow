import pytest


def get_ai_user(client, email="ai_user@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"name": "AI User", "email": email, "password": "Password123!"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ai_chat_records_samosa_expense(client):
    headers = get_ai_user(client, "samosa_test@example.com")

    # User message: "Aaj maine 20 ka samosa khaya"
    res = client.post(
        "/api/v1/ai/chat",
        json={"message": "Aaj maine 20 ka samosa khaya"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "transaction"
    assert len(data["recorded_transactions"]) == 1

    tx = data["recorded_transactions"][0]
    # ₹20 = 2000 paise
    assert tx["amount"] == 2000
    assert tx["amount_in_rupees"] == 20.0
    assert tx["type"] == "expense"
    assert tx["category"]["name"] == "Food"

    # Verify transaction is in user's database records
    tx_list = client.get("/api/v1/transactions", headers=headers).json()
    assert tx_list["total"] == 1
    assert tx_list["items"][0]["amount"] == 2000


def test_ai_chat_records_salary_income(client):
    headers = get_ai_user(client, "salary_ai_test@example.com")

    # User message: "Received 30000 rupees as salary"
    res = client.post(
        "/api/v1/ai/chat",
        json={"message": "Received 30000 rupees as salary"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "transaction"
    assert len(data["recorded_transactions"]) == 1

    tx = data["recorded_transactions"][0]
    # ₹30,000 = 3000000 paise
    assert tx["amount"] == 3000000
    assert tx["type"] == "income"
    assert tx["category"]["name"] == "Salary"


def test_ai_chat_records_savings_deposit(client):
    headers = get_ai_user(client, "savings_ai_test@example.com")

    # Initialize first
    client.post("/api/v1/savings/initialize", json={"amount": 1000000}, headers=headers)

    # User message: "Savings mein 5000 jama kiye"
    res = client.post(
        "/api/v1/ai/chat",
        json={"message": "Savings mein 5000 jama kiye"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "savings"
    assert data["recorded_savings"] is not None
    assert data["recorded_savings"]["amount"] == 500000  # ₹5,000 in paise
    assert data["recorded_savings"]["type"] == "deposit"

    # Verify savings summary
    sav_res = client.get("/api/v1/savings/summary", headers=headers).json()
    assert sav_res["current_savings"] == 1500000  # 10,000 + 5,000


def test_ai_chat_clarification_on_missing_amount(client):
    headers = get_ai_user(client, "clarify_ai_test@example.com")

    # Missing amount
    res = client.post(
        "/api/v1/ai/chat",
        json={"message": "Maine chai pee li"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["requires_clarification"] is True
    assert len(data["recorded_transactions"]) == 0
