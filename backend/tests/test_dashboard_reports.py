import datetime
import pytest


def setup_dashboard_user(client, email="dash_user@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Dashboard User", "email": email, "password": "Password123!"},
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
    travel_cat = next(c for c in cats if c["name"] == "Travel")
    salary_cat = next(c for c in cats if c["name"] == "Salary")

    return headers, food_cat["id"], travel_cat["id"], salary_cat["id"]


def test_dashboard_summary_and_reports(client):
    headers, food_id, travel_id, salary_id = setup_dashboard_user(client, "dash_metrics@example.com")
    today = datetime.date.today()
    date_str = str(today)

    # 1. Initialize savings: ₹50,000 (5000000 paise)
    client.post(
        "/api/v1/savings/initialize",
        json={"amount": 5000000},
        headers=headers,
    )

    # 2. Add Income: ₹40,000 (4000000 paise)
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": salary_id,
            "amount": 4000000,
            "type": "income",
            "description": "November Salary",
            "transaction_date": date_str,
        },
        headers=headers,
    )

    # 3. Add Expense 1: ₹3,000 Food (300000 paise)
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": food_id,
            "amount": 300000,
            "type": "expense",
            "description": "Groceries & Cafe",
            "transaction_date": date_str,
        },
        headers=headers,
    )

    # 4. Add Expense 2: ₹1,000 Travel (100000 paise)
    client.post(
        "/api/v1/transactions",
        json={
            "category_id": travel_id,
            "amount": 100000,
            "type": "expense",
            "description": "Metro & Fuel",
            "transaction_date": date_str,
        },
        headers=headers,
    )

    # Check Dashboard Summary
    dash_res = client.get(f"/api/v1/dashboard/summary?month={today.month}&year={today.year}", headers=headers)
    assert dash_res.status_code == 200
    summary = dash_res.json()

    # Calculations:
    # Income: 4000000 (₹40,000)
    # Expense: 300000 + 100000 = 400000 (₹4,000)
    # Monthly balance: 4000000 - 400000 = 3600000 (₹36,000)
    # Savings: 5000000 (₹50,000)
    assert summary["total_income"] == 4000000
    assert summary["total_income_in_rupees"] == 40000.0
    assert summary["total_expenses"] == 400000
    assert summary["total_expenses_in_rupees"] == 4000.0
    assert summary["monthly_balance"] == 3600000
    assert summary["monthly_balance_in_rupees"] == 36000.0
    assert summary["current_savings"] == 5000000
    assert summary["current_savings_in_rupees"] == 50000.0
    assert len(summary["recent_transactions"]) == 3

    # Check Category Breakdown
    cat_res = client.get(f"/api/v1/dashboard/category-breakdown?month={today.month}&year={today.year}", headers=headers)
    assert cat_res.status_code == 200
    breakdown = cat_res.json()
    assert len(breakdown) == 2
    # Food is 75% (3000 / 4000), Travel is 25% (1000 / 4000)
    food_stat = next(b for b in breakdown if b["category_name"] == "Food")
    travel_stat = next(b for b in breakdown if b["category_name"] == "Travel")
    assert food_stat["percentage"] == 75.0
    assert food_stat["total_amount"] == 300000
    assert travel_stat["percentage"] == 25.0
    assert travel_stat["total_amount"] == 100000

    # Check Monthly Trends
    trend_res = client.get("/api/v1/dashboard/monthly-trends?months=3", headers=headers)
    assert trend_res.status_code == 200
    trends = trend_res.json()
    assert len(trends) == 3
    current_month_trend = trends[-1]
    assert current_month_trend["income"] == 4000000
    assert current_month_trend["expense"] == 400000

    # Check Monthly Report
    report_res = client.get(f"/api/v1/reports/monthly?month={today.month}&year={today.year}", headers=headers)
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["total_income"] == 4000000
    assert report["total_expenses"] == 400000
    assert report["net_savings"] == 3600000
    # Savings rate = (36000 / 40000) * 100 = 90.0%
    assert report["savings_rate_percentage"] == 90.0
    assert len(report["category_breakdown"]) == 2
    assert len(report["daily_spending"]) >= 1

