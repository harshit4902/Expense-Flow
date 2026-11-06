import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.savings import SavingsTransaction
from app.schemas.savings import (
    SavingsInitializeRequest,
    SavingsDepositRequest,
    SavingsWithdrawRequest,
    SavingsBalanceAdjustmentRequest,
    SavingsTransactionResponse,
    SavingsSummaryResponse,
)


def calculate_savings_summary(db: Session, user_id: int) -> SavingsSummaryResponse:
    """Calculates savings statistics from the user's savings ledger.
    Formula:
    Current Savings = Initial Savings + Total Deposits - Total Withdrawals + Net Adjustments
    """
    records = (
        db.query(SavingsTransaction)
        .filter(SavingsTransaction.user_id == user_id)
        .order_by(SavingsTransaction.transaction_date.asc(), SavingsTransaction.id.asc())
        .all()
    )

    initial_savings = 0
    total_deposits = 0
    total_withdrawals = 0
    net_adjustments = 0
    has_initial = False

    for r in records:
        if r.type == "initial_balance":
            initial_savings += r.amount
            has_initial = True
        elif r.type == "deposit":
            total_deposits += r.amount
        elif r.type == "withdrawal":
            total_withdrawals += r.amount
        elif r.type == "balance_adjustment":
            net_adjustments += r.amount

    current_savings = initial_savings + total_deposits - total_withdrawals + net_adjustments

    return SavingsSummaryResponse(
        current_savings=current_savings,
        current_savings_in_rupees=round(current_savings / 100.0, 2),
        initial_savings=initial_savings,
        initial_savings_in_rupees=round(initial_savings / 100.0, 2),
        total_deposits=total_deposits,
        total_deposits_in_rupees=round(total_deposits / 100.0, 2),
        total_withdrawals=total_withdrawals,
        total_withdrawals_in_rupees=round(total_withdrawals / 100.0, 2),
        net_adjustments=net_adjustments,
        net_adjustments_in_rupees=round(net_adjustments / 100.0, 2),
        has_initial_balance=has_initial,
    )


def initialize_savings(
    db: Session,
    user_id: int,
    data: SavingsInitializeRequest,
) -> SavingsTransactionResponse:
    """Sets initial savings balance for a user.
    If already initialized, raises an exception (user should use balance adjustment instead).
    """
    existing_initial = (
        db.query(SavingsTransaction)
        .filter(
            SavingsTransaction.user_id == user_id,
            SavingsTransaction.type == "initial_balance",
        )
        .first()
    )
    if existing_initial:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial savings balance has already been set. Use balance adjustment to correct.",
        )

    tx_date = data.transaction_date or datetime.date.today()
    record = SavingsTransaction(
        user_id=user_id,
        amount=data.amount,
        type="initial_balance",
        description=data.description or "Initial savings account balance",
        transaction_date=tx_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return SavingsTransactionResponse.from_orm_model(record)


def add_deposit(
    db: Session,
    user_id: int,
    data: SavingsDepositRequest,
) -> SavingsTransactionResponse:
    """Records a new savings deposit."""
    tx_date = data.transaction_date or datetime.date.today()
    record = SavingsTransaction(
        user_id=user_id,
        amount=data.amount,
        type="deposit",
        description=data.description or "Savings deposit",
        transaction_date=tx_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return SavingsTransactionResponse.from_orm_model(record)


def add_withdrawal(
    db: Session,
    user_id: int,
    data: SavingsWithdrawRequest,
) -> SavingsTransactionResponse:
    """Records a savings withdrawal. Ensures the user has sufficient savings balance."""
    summary = calculate_savings_summary(db, user_id)
    if data.amount > summary.current_savings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient savings balance. Current balance is ₹{summary.current_savings_in_rupees:,.2f}.",
        )

    tx_date = data.transaction_date or datetime.date.today()
    record = SavingsTransaction(
        user_id=user_id,
        amount=data.amount,
        type="withdrawal",
        description=data.description or "Savings withdrawal",
        transaction_date=tx_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return SavingsTransactionResponse.from_orm_model(record)


def adjust_savings_balance(
    db: Session,
    user_id: int,
    data: SavingsBalanceAdjustmentRequest,
) -> Tuple[SavingsTransactionResponse, SavingsSummaryResponse]:
    """Adjusts the savings balance to match a user-reported current balance.
    Calculates the delta between target and current balance:
    delta = target_balance - current_savings
    Records a balance_adjustment entry with the delta (which can be positive or negative)
    without modifying prior ledger history.
    """
    summary = calculate_savings_summary(db, user_id)
    diff = data.target_balance - summary.current_savings

    if diff == 0:
        # Current balance already matches target
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reported balance matches the current recorded savings balance.",
        )

    tx_date = data.transaction_date or datetime.date.today()
    record = SavingsTransaction(
        user_id=user_id,
        amount=diff,  # stored as positive or negative delta in paise
        type="balance_adjustment",
        description=data.description or f"Balance adjustment to ₹{data.target_balance / 100.0:,.2f}",
        transaction_date=tx_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    new_summary = calculate_savings_summary(db, user_id)
    return SavingsTransactionResponse.from_orm_model(record), new_summary


def get_savings_history(
    db: Session,
    user_id: int,
) -> List[SavingsTransactionResponse]:
    """Retrieves full savings ledger history ordered chronologically."""
    records = (
        db.query(SavingsTransaction)
        .filter(SavingsTransaction.user_id == user_id)
        .order_by(SavingsTransaction.transaction_date.desc(), SavingsTransaction.id.desc())
        .all()
    )
    return [SavingsTransactionResponse.from_orm_model(r) for r in records]

