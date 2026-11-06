from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    CategoryExpenseBreakdown,
    MonthlyTrendItem,
    SavingsTrendItem,
)
from app.services import report_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (default: current)"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Target year (default: current)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all dashboard summary metrics: income, expenses, savings, monthly balance, budget utilization, and recent transactions."""
    return report_service.get_dashboard_summary(db, current_user.id, month=month, year=year)


@router.get("/category-breakdown", response_model=List[CategoryExpenseBreakdown])
def get_category_breakdown(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve category-wise expense breakdown with amounts and percentages for pie charts."""
    return report_service.get_category_breakdown(db, current_user.id, month=month, year=year)


@router.get("/monthly-trends", response_model=List[MonthlyTrendItem])
def get_monthly_trends(
    months: int = Query(6, ge=1, le=24, description="Number of past months to retrieve"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve income vs expense monthly trends for bar / area charts."""
    return report_service.get_monthly_trends(db, current_user.id, months_count=months)


@router.get("/savings-trends", response_model=List[SavingsTrendItem])
def get_savings_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve running savings balance history for savings trend line charts."""
    return report_service.get_savings_trends(db, current_user.id)

