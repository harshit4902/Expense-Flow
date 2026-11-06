from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.dashboard import (
    MonthlyReportResponse,
    CategoryExpenseBreakdown,
)
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly", response_model=MonthlyReportResponse)
def get_monthly_report(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive monthly financial report with savings rate, category breakdown, and daily spending."""
    return report_service.get_monthly_report(db, current_user.id, month=month, year=year)


@router.get("/category-wise", response_model=List[CategoryExpenseBreakdown])
def get_category_wise_report(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve category-wise financial expenditure report."""
    return report_service.get_category_breakdown(db, current_user.id, month=month, year=year)

