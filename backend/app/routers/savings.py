from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.savings import (
    SavingsInitializeRequest,
    SavingsDepositRequest,
    SavingsWithdrawRequest,
    SavingsBalanceAdjustmentRequest,
    SavingsTransactionResponse,
    SavingsSummaryResponse,
    SavingsHistoryResponse,
)
from app.services import savings_service

router = APIRouter(prefix="/savings", tags=["Savings"])


@router.get("/summary", response_model=SavingsSummaryResponse)
def get_savings_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current savings balance, initial balance, total deposits, and total withdrawals."""
    return savings_service.calculate_savings_summary(db, current_user.id)


@router.get("/history", response_model=SavingsHistoryResponse)
def get_savings_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full ledger history of all savings transactions and adjustments."""
    items = savings_service.get_savings_history(db, current_user.id)
    return {
        "items": items,
        "total": len(items),
    }


@router.post("/initialize", response_model=SavingsTransactionResponse, status_code=status.HTTP_201_CREATED)
def initialize_savings(
    data: SavingsInitializeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set the initial savings balance (e.g. during onboarding)."""
    return savings_service.initialize_savings(db, current_user.id, data)


@router.post("/deposit", response_model=SavingsTransactionResponse, status_code=status.HTTP_201_CREATED)
def add_savings_deposit(
    data: SavingsDepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a new savings deposit."""
    return savings_service.add_deposit(db, current_user.id, data)


@router.post("/withdraw", response_model=SavingsTransactionResponse, status_code=status.HTTP_201_CREATED)
def add_savings_withdrawal(
    data: SavingsWithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a savings withdrawal (fails if balance is insufficient)."""
    return savings_service.add_withdrawal(db, current_user.id, data)


@router.patch("/balance", response_model=SavingsTransactionResponse)
def adjust_savings_balance(
    data: SavingsBalanceAdjustmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Adjust savings balance to match reported current balance via a delta adjustment."""
    record, _ = savings_service.adjust_savings_balance(db, current_user.id, data)
    return record

