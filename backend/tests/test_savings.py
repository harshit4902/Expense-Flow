import pytest


def get_savings_user(client, email="savings_test@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Savings User", "email": email, "password": "Password123!"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_initial_savings_flow(client):
    headers = get_savings_user(client, "sav_init@example.com")

    # Initially balance is 0
    res0 = client.get("/api/v1/savings/summary", headers=headers)
    assert res0.status_code == 200
    assert res0.json()["current_savings"] == 0
    assert res0.json()["has_initial_balance"] is False

    # Initialize with ₹50,000 (5,000,000 paise)
    res1 = client.post(
        "/api/v1/savings/initialize",
        json={"amount": 5000000, "description": "Starting savings"},
        headers=headers,
    )
    assert res1.status_code == 201
    assert res1.json()["amount"] == 5000000
    assert res1.json()["amount_in_rupees"] == 50000.0

    # Summary check
    res2 = client.get("/api/v1/savings/summary", headers=headers)
    assert res2.status_code == 200
    summary = res2.json()
    assert summary["current_savings"] == 5000000
    assert summary["current_savings_in_rupees"] == 50000.0
    assert summary["has_initial_balance"] is True

    # Re-initialization should fail
    res3 = client.post(
        "/api/v1/savings/initialize",
        json={"amount": 1000000},
        headers=headers,
    )
    assert res3.status_code == 400
    assert "already been set" in res3.json()["detail"]


def test_savings_deposit_and_withdrawal(client):
    headers = get_savings_user(client, "sav_dep_with@example.com")

    # 1. Initialize with ₹20,000 (2000000 paise)
    client.post(
        "/api/v1/savings/initialize",
        json={"amount": 2000000},
        headers=headers,
    )

    # 2. Deposit ₹5,000 (500000 paise)
    res_dep = client.post(
        "/api/v1/savings/deposit",
        json={"amount": 500000, "description": "Saved from bonus"},
        headers=headers,
    )
    assert res_dep.status_code == 201

    # Check balance -> ₹25,000
    summary1 = client.get("/api/v1/savings/summary", headers=headers).json()
    assert summary1["current_savings"] == 2500000
    assert summary1["total_deposits"] == 500000

    # 3. Withdraw ₹2,000 (200000 paise)
    res_with = client.post(
        "/api/v1/savings/withdraw",
        json={"amount": 200000, "description": "Emergency expense withdrawal"},
        headers=headers,
    )
    assert res_with.status_code == 201

    # Check balance -> ₹23,000
    summary2 = client.get("/api/v1/savings/summary", headers=headers).json()
    assert summary2["current_savings"] == 2300000
    assert summary2["total_withdrawals"] == 200000


def test_savings_withdrawal_insufficient_funds(client):
    headers = get_savings_user(client, "sav_overdraw@example.com")

    # Set balance to ₹1,000 (100000 paise)
    client.post(
        "/api/v1/savings/initialize",
        json={"amount": 100000},
        headers=headers,
    )

    # Attempt to withdraw ₹5,000 (500000 paise)
    res = client.post(
        "/api/v1/savings/withdraw",
        json={"amount": 500000},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Insufficient savings balance" in res.json()["detail"]


def test_savings_balance_adjustment(client):
    headers = get_savings_user(client, "sav_adjust@example.com")

    # User starts with ₹50,000
    client.post(
        "/api/v1/savings/initialize",
        json={"amount": 5000000},
        headers=headers,
    )

    # User states: "My actual savings balance is ₹75,000"
    # Adjustment target: 7500000 paise (delta should be +2500000 paise)
    res_adj = client.patch(
        "/api/v1/savings/balance",
        json={"target_balance": 7500000, "description": "Bank statement true-up"},
        headers=headers,
    )
    assert res_adj.status_code == 200
    data = res_adj.json()
    assert data["amount"] == 2500000
    assert data["type"] == "balance_adjustment"

    # Verify summary reflects ₹75,000
    summary = client.get("/api/v1/savings/summary", headers=headers).json()
    assert summary["current_savings"] == 7500000
    assert summary["current_savings_in_rupees"] == 75000.0
    assert summary["net_adjustments"] == 2500000

    # User then states: "Actually balance dropped to ₹70,000" (negative delta: -500000 paise)
    res_adj2 = client.patch(
        "/api/v1/savings/balance",
        json={"target_balance": 7000000},
        headers=headers,
    )
    assert res_adj2.status_code == 200
    assert res_adj2.json()["amount"] == -500000

    summary2 = client.get("/api/v1/savings/summary", headers=headers).json()
    assert summary2["current_savings"] == 7000000


def test_savings_history_and_isolation(client):
    headers1 = get_savings_user(client, "sav_iso1@example.com")
    headers2 = get_savings_user(client, "sav_iso2@example.com")

    client.post(
        "/api/v1/savings/initialize",
        json={"amount": 1000000},
        headers=headers1,
    )
    client.post(
        "/api/v1/savings/deposit",
        json={"amount": 500000},
        headers=headers1,
    )

    # User 1 history has 2 records
    hist1 = client.get("/api/v1/savings/history", headers=headers1).json()
    assert hist1["total"] == 2

    # User 2 history is completely isolated (0 records)
    hist2 = client.get("/api/v1/savings/history", headers=headers2).json()
    assert hist2["total"] == 0

