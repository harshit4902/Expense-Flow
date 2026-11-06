import datetime
import pytest


def setup_budget_user(client, email="budget_user@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Budget User", "email": email, "password": "Password123!"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cats = client.get("/api/v1/categories", headers=headers).json()
    food_cat = next(c for c in cats if c["name"] == "Food")
    travel_cat = next(c for c in cats if c["name"] == "Travel")
    salary_cat = next(c for c in cats if c["name"] == "Salary")
    return headers, food_cat["id"], travel_cat["id"], salary_cat["id"]


def test_create_and_calculate_budgets(client):
    headers, food_id, travel_id, _ = setup_budget_user(client, "bg_calc@example.com")
    today = datetime.date.today()
    month, year = today.month, today.year

    # 1. Create Overall Budget: ₹15,000 (1500000 paise)
    res_overall = client.post(
        "/api/v1/budgets",
        json={"amount": 1500000, "month": month, "year": year, "category_id": None},
        headers=headers,
    )
    assert res_overall.status_code == 201
    assert res_overall.json()["is_overall"] is True
    assert res_overall.json()["amount"] == 1500000

    # 2. Create Category Budget for Food: ₹4,000 (400000 paise)
    res_food = client.post(
        "/api/v1/budgets",
        json={"amount": 400000, "month": month, "year": year, "category_id": food_id},
        headers=headers,
    )
    assert res_food.status_code == 201
    assert res_food.json()["category_name"] == "Food"

    # 3. Add Expense to Food: ₹3,500 (350000 paise -> 87.5% used, should trigger 'warning')
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": food_id,
            "amount": 350000,
            "type": "expense",
            "description": "Weekly Groceries",
            "transaction_date": str(today),
        },
        headers=headers,
    )

    # 4. Fetch Budgets
    summary_res = client.get(f"/api/v1/budgets?month={month}&year={year}", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()

    # Overall budget calculations
    assert summary["overall_budget"]["spent"] == 350000
    assert summary["overall_budget"]["remaining"] == 1150000
    assert summary["overall_budget"]["percentage_used"] == round(350000 / 1500000 * 100.0, 2)
    assert summary["overall_budget"]["warning_status"] == "normal"

    # Category budget calculations
    cat_b = summary["category_budgets"][0]
    assert cat_b["spent"] == 350000
    assert cat_b["percentage_used"] == 87.5
    assert cat_b["warning_status"] == "warning"  # >=80%

    assert summary["has_warning_any"] is True
    assert summary["has_exceeded_any"] is False


def test_budget_exceeded_warning(client):
    headers, food_id, _, _ = setup_budget_user(client, "bg_exceed@example.com")
    today = datetime.date.today()
    month, year = today.month, today.year

    # Create Category Budget for Food: ₹2,000 (200000 paise)
    client.post(
        "/api/v1/budgets",
        json={"amount": 200000, "month": month, "year": year, "category_id": food_id},
        headers=headers,
    )

    # Spend ₹2,500 (250000 paise -> 125% used, triggers 'exceeded')
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": food_id,
            "amount": 250000,
            "type": "expense",
            "description": "Dining out",
            "transaction_date": str(today),
        },
        headers=headers,
    )

    summary = client.get(f"/api/v1/budgets?month={month}&year={year}", headers=headers).json()
    cat_b = summary["category_budgets"][0]
    assert cat_b["percentage_used"] == 125.0
    assert cat_b["warning_status"] == "exceeded"
    assert cat_b["remaining"] == 0
    assert summary["has_exceeded_any"] is True


def test_duplicate_budget_prevention(client):
    headers, food_id, _, _ = setup_budget_user(client, "bg_dup@example.com")
    today = datetime.date.today()
    month, year = today.month, today.year

    payload = {"amount": 500000, "month": month, "year": year, "category_id": food_id}
    res1 = client.post("/api/v1/budgets", json=payload, headers=headers)
    assert res1.status_code == 201

    # Second creation for same month/year/category must fail
    res2 = client.post("/api/v1/budgets", json=payload, headers=headers)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_cannot_budget_income_category(client):
    headers, _, _, salary_id = setup_budget_user(client, "bg_income_cat@example.com")
    today = datetime.date.today()

    res = client.post(
        "/api/v1/budgets",
        json={"amount": 500000, "month": today.month, "year": today.year, "category_id": salary_id},
        headers=headers,
    )
    assert res.status_code == 400
    assert "only be created for expense categories" in res.json()["detail"]

