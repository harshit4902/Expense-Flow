import calendar
import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetSummary,
)
from app.schemas.category import CategoryResponse


def get_month_date_range(year: int, month: int):
    """Returns start and end dates for a month."""
    num_days = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, 1), datetime.date(year, month, num_days)


def calculate_budget_response(db: Session, budget: Budget) -> BudgetResponse:
    """Calculates spending, remaining balance, utilization percentage, and warning status for a budget."""
    start_date, end_date = get_month_date_range(budget.year, budget.month)

    query = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == budget.user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    if budget.category_id is not None:
        query = query.filter(Transaction.category_id == budget.category_id)

    spent = query.scalar()
    remaining = max(0, budget.amount - spent)
    pct_used = round((spent / budget.amount * 100.0), 2) if budget.amount > 0 else 0.0

    if pct_used > 100.0:
        warning_status = "exceeded"
    elif pct_used >= 80.0:
        warning_status = "warning"
    else:
        warning_status = "normal"

    cat_resp = CategoryResponse.model_validate(budget.category) if budget.category else None
    cat_name = budget.category.name if budget.category else None

    return BudgetResponse(
        id=budget.id,
        user_id=budget.user_id,
        category_id=budget.category_id,
        category_name=cat_name,
        is_overall=budget.category_id is None,
        amount=budget.amount,
        amount_in_rupees=round(budget.amount / 100.0, 2),
        spent=spent,
        spent_in_rupees=round(spent / 100.0, 2),
        remaining=remaining,
        remaining_in_rupees=round(remaining / 100.0, 2),
        percentage_used=pct_used,
        warning_status=warning_status,
        month=budget.month,
        year=budget.year,
        created_at=budget.created_at,
        category=cat_resp,
    )


def create_budget(db: Session, user_id: int, budget_in: BudgetCreate) -> BudgetResponse:
    """Creates a new overall or category-specific monthly budget."""
    # If category_id provided, ensure category exists, belongs to user, and is expense
    if budget_in.category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == budget_in.category_id, Category.user_id == user_id)
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )
        if category.type != "expense":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Budgets can only be created for expense categories.",
            )

    # Check for existing budget for the same month, year, and category (or overall)
    existing_query = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.month == budget_in.month,
        Budget.year == budget_in.year,
    )
    if budget_in.category_id is None:
        existing = existing_query.filter(Budget.category_id.is_(None)).first()
    else:
        existing = existing_query.filter(Budget.category_id == budget_in.category_id).first()

    if existing:
        budget_type = "Overall monthly budget" if budget_in.category_id is None else f"Budget for category '{existing.category.name}'"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{budget_type} already exists for {budget_in.month}/{budget_in.year}.",
        )

    budget = Budget(
        user_id=user_id,
        category_id=budget_in.category_id,
        amount=budget_in.amount,
        month=budget_in.month,
        year=budget_in.year,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return calculate_budget_response(db, budget)


def get_budgets(
    db: Session,
    user_id: int,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> BudgetSummary:
    """Retrieves all budgets for a given month and year, computing overall and category metrics without double counting."""
    today = datetime.date.today()
    target_month = month or today.month
    target_year = year or today.year

    budgets = (
        db.query(Budget)
        .options(joinedload(Budget.category))
        .filter(
            Budget.user_id == user_id,
            Budget.month == target_month,
            Budget.year == target_year,
        )
        .all()
    )

    overall_budget_model = next((b for b in budgets if b.category_id is None), None)
    category_budget_models = [b for b in budgets if b.category_id is not None]

    overall_resp = calculate_budget_response(db, overall_budget_model) if overall_budget_model else None
    cat_resps = [calculate_budget_response(db, b) for b in category_budget_models]

    start_date, end_date = get_month_date_range(target_year, target_month)
    total_month_spent = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .scalar()
    )

    # Do not double-count: if overall budget exists, total budget amount is overall budget
    # Otherwise, sum of category budgets
    if overall_resp:
        total_budget_amount = overall_resp.amount
    else:
        total_budget_amount = sum(c.amount for c in cat_resps)

    total_remaining = max(0, total_budget_amount - total_month_spent)

    all_resps = ([overall_resp] if overall_resp else []) + cat_resps
    has_exceeded = any(b.warning_status == "exceeded" for b in all_resps)
    has_warning = any(b.warning_status in ["warning", "exceeded"] for b in all_resps)

    return BudgetSummary(
        month=target_month,
        year=target_year,
        overall_budget=overall_resp,
        category_budgets=cat_resps,
        total_budget_amount=total_budget_amount,
        total_budget_amount_in_rupees=round(total_budget_amount / 100.0, 2),
        total_spent=total_month_spent,
        total_spent_in_rupees=round(total_month_spent / 100.0, 2),
        total_remaining=total_remaining,
        total_remaining_in_rupees=round(total_remaining / 100.0, 2),
        has_exceeded_any=has_exceeded,
        has_warning_any=has_warning,
    )


def update_budget(
    db: Session,
    budget_id: int,
    user_id: int,
    budget_in: BudgetUpdate,
) -> BudgetResponse:
    """Updates an existing budget."""
    budget = (
        db.query(Budget)
        .options(joinedload(Budget.category))
        .filter(Budget.id == budget_id, Budget.user_id == user_id)
        .first()
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found.",
        )

    if budget_in.amount is not None:
        budget.amount = budget_in.amount

    db.commit()
    db.refresh(budget)
    return calculate_budget_response(db, budget)


def delete_budget(db: Session, budget_id: int, user_id: int) -> None:
    """Deletes a budget."""
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == user_id)
        .first()
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found.",
        )
    db.delete(budget)
    db.commit()

