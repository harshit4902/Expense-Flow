import datetime
import calendar
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract

from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.savings import SavingsTransaction
from app.services.savings_service import calculate_savings_summary
from app.schemas.transaction import TransactionResponse
from app.schemas.dashboard import (
    CategoryExpenseBreakdown,
    MonthlyTrendItem,
    SavingsTrendItem,
    DashboardSummaryResponse,
    MonthlyReportResponse,
)


def get_month_date_range(year: int, month: int):
    """Returns the start and end dates for a given month and year."""
    num_days = calendar.monthrange(year, month)[1]
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)
    return start_date, end_date


def get_dashboard_summary(
    db: Session,
    user_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> DashboardSummaryResponse:
    """Calculates all key metrics for the user's dashboard cards."""
    today = datetime.date.today()
    target_month = month or today.month
    target_year = year or today.year
    start_date, end_date = get_month_date_range(target_year, target_month)

    # 1. Total Income & Total Expenses for target month
    income_sum = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    expense_sum = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    # 2. Monthly Balance = Income - Expenses
    monthly_balance = income_sum - expense_sum

    # 3. Current Savings balance
    savings_summary = calculate_savings_summary(db, user_id)
    current_savings = savings_summary.current_savings

    # 4. Monthly Budget info
    # Overall budget (category_id is NULL)
    overall_budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.month == target_month,
            Budget.year == target_year,
            Budget.category_id.is_(None),
        )
        .first()
    )

    # If no overall budget, sum category-specific budgets to avoid double-counting
    if overall_budget:
        total_budget = overall_budget.amount
    else:
        cat_budgets_sum = (
            db.query(func.coalesce(func.sum(Budget.amount), 0))
            .filter(
                Budget.user_id == user_id,
                Budget.month == target_month,
                Budget.year == target_year,
                Budget.category_id.isnot(None),
            )
            .scalar()
        )
        total_budget = cat_budgets_sum

    budget_spent = expense_sum
    budget_remaining = max(0, total_budget - budget_spent)

    # 5. Recent 5 Transactions
    recent_records = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .limit(5)
        .all()
    )
    recent_txs = [TransactionResponse.from_orm_model(tx) for tx in recent_records]

    return DashboardSummaryResponse(
        month=target_month,
        year=target_year,
        total_income=income_sum,
        total_income_in_rupees=round(income_sum / 100.0, 2),
        total_expenses=expense_sum,
        total_expenses_in_rupees=round(expense_sum / 100.0, 2),
        monthly_balance=monthly_balance,
        monthly_balance_in_rupees=round(monthly_balance / 100.0, 2),
        current_savings=current_savings,
        current_savings_in_rupees=round(current_savings / 100.0, 2),
        total_budget=total_budget,
        total_budget_in_rupees=round(total_budget / 100.0, 2),
        budget_spent=budget_spent,
        budget_spent_in_rupees=round(budget_spent / 100.0, 2),
        budget_remaining=budget_remaining,
        budget_remaining_in_rupees=round(budget_remaining / 100.0, 2),
        recent_transactions=recent_txs,
    )


def get_category_breakdown(
    db: Session,
    user_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> List[CategoryExpenseBreakdown]:
    """Computes category-wise expense breakdown with amounts and percentages."""
    today = datetime.date.today()
    target_month = month or today.month
    target_year = year or today.year
    start_date, end_date = get_month_date_range(target_year, target_month)

    total_expense = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    rows = (
        db.query(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.sum(Transaction.amount).label("total_amount"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    results = []
    for r in rows:
        pct = round((r.total_amount / total_expense * 100.0), 2) if total_expense > 0 else 0.0
        results.append(
            CategoryExpenseBreakdown(
                category_id=r.category_id,
                category_name=r.category_name,
                total_amount=r.total_amount,
                total_amount_in_rupees=round(r.total_amount / 100.0, 2),
                percentage=pct,
            )
        )
    return results


def get_monthly_trends(
    db: Session,
    user_id: int,
    months_count: int = 6,
) -> List[MonthlyTrendItem]:
    """Calculates income vs expense monthly trends for the last N months."""
    today = datetime.date.today()
    trend_data = []

    # Iterate over the past `months_count` months
    for i in range(months_count - 1, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        start_date, end_date = get_month_date_range(year, month)

        income = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "income",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .scalar()
        )

        expense = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
            )
            .scalar()
        )

        month_label = f"{calendar.month_abbr[month]} {year}"
        net = income - expense

        trend_data.append(
            MonthlyTrendItem(
                month=month,
                year=year,
                month_name=month_label,
                income=income,
                income_in_rupees=round(income / 100.0, 2),
                expense=expense,
                expense_in_rupees=round(expense / 100.0, 2),
                net_savings_or_balance=net,
                net_savings_or_balance_in_rupees=round(net / 100.0, 2),
            )
        )

    return trend_data


def get_savings_trends(
    db: Session,
    user_id: int,
) -> List[SavingsTrendItem]:
    """Calculates running savings balance history chronologically."""
    records = (
        db.query(SavingsTransaction)
        .filter(SavingsTransaction.user_id == user_id)
        .order_by(SavingsTransaction.transaction_date.asc(), SavingsTransaction.id.asc())
        .all()
    )

    running_balance = 0
    trends = []
    for r in records:
        if r.type == "initial_balance":
            running_balance += r.amount
        elif r.type == "deposit":
            running_balance += r.amount
        elif r.type == "withdrawal":
            running_balance -= r.amount
        elif r.type == "balance_adjustment":
            running_balance += r.amount

        trends.append(
            SavingsTrendItem(
                date=r.transaction_date,
                running_balance=running_balance,
                running_balance_in_rupees=round(running_balance / 100.0, 2),
                change_type=r.type,
                change_amount=r.amount,
            )
        )
    return trends


def get_monthly_report(
    db: Session,
    user_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> MonthlyReportResponse:
    """Generates detailed monthly report including daily spending distribution and savings rate."""
    today = datetime.date.today()
    target_month = month or today.month
    target_year = year or today.year
    start_date, end_date = get_month_date_range(target_year, target_month)

    # 1. Total income & expenses
    income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    expense = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    net_savings = income - expense
    savings_rate = round((net_savings / income * 100.0), 2) if income > 0 else 0.0

    # 2. Category breakdown
    cat_breakdown = get_category_breakdown(db, user_id, target_month, target_year)

    # 3. Daily spending
    daily_rows = (
        db.query(
            Transaction.transaction_date.label("date"),
            func.sum(Transaction.amount).label("amount"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Transaction.transaction_date)
        .order_by(Transaction.transaction_date.asc())
        .all()
    )
    daily_spending = [
        {"date": str(r.date), "amount": r.amount, "amount_in_rupees": round(r.amount / 100.0, 2)}
        for r in daily_rows
    ]

    return MonthlyReportResponse(
        month=target_month,
        year=target_year,
        total_income=income,
        total_income_in_rupees=round(income / 100.0, 2),
        total_expenses=expense,
        total_expenses_in_rupees=round(expense / 100.0, 2),
        net_savings=net_savings,
        net_savings_in_rupees=round(net_savings / 100.0, 2),
        savings_rate_percentage=savings_rate,
        category_breakdown=cat_breakdown,
        daily_spending=daily_spending,
    )

