import datetime
import calendar
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.savings import SavingsTransaction
from app.models.transaction import Transaction
from app.schemas.savings import (
    SavingsInitializeRequest,
    SavingsDepositRequest,
    SavingsWithdrawRequest,
    SavingsBalanceAdjustmentRequest,
    SavingsTransactionResponse,
    SavingsSummaryResponse,
)


def auto_rollover_monthly_savings(db: Session, user_id: int) -> None:
    """Checks for completed past calendar months that had a positive monthly balance
    (Income - Expenses > 0) and automatically deposits the net balance into the savings ledger
    under the name '{Month Name} {Year} Saving' (e.g. 'October 2026 Saving').
    Idempotent: prevents duplicate deposits for the same month.
    """
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month

    # Find earliest transaction date for the user to determine which past months exist
    earliest_tx = (
        db.query(func.min(Transaction.transaction_date))
        .filter(Transaction.user_id == user_id)
        .scalar()
    )
    if not earliest_tx:
        return

    # Check each month from earliest transaction month up to last month
    start_y = earliest_tx.year
    start_m = earliest_tx.month

    check_y = start_y
    check_m = start_m

    while (check_y < current_year) or (check_y == current_year and check_m < current_month):
        month_name = calendar.month_name[check_m]
        rollover_tag = f"{month_name} {check_y} Saving"

        # Check if rollover deposit already exists
        existing_deposit = (
            db.query(SavingsTransaction)
            .filter(
                SavingsTransaction.user_id == user_id,
                SavingsTransaction.type == "deposit",
                SavingsTransaction.description == rollover_tag,
            )
            .first()
        )

        if not existing_deposit:
            # Calculate total income and total expenses for this month
            num_days = calendar.monthrange(check_y, check_m)[1]
            m_start = datetime.date(check_y, check_m, 1)
            m_end = datetime.date(check_y, check_m, num_days)

            income_sum = (
                db.query(func.coalesce(func.sum(Transaction.amount), 0))
                .filter(
                    Transaction.user_id == user_id,
                    Transaction.type == "income",
                    Transaction.transaction_date >= m_start,
                    Transaction.transaction_date <= m_end,
                )
                .scalar()
            )

            expense_sum = (
                db.query(func.coalesce(func.sum(Transaction.amount), 0))
                .filter(
                    Transaction.user_id == user_id,
                    Transaction.type == "expense",
                    Transaction.transaction_date >= m_start,
                    Transaction.transaction_date <= m_end,
                )
                .scalar()
            )

            net_month_balance = income_sum - expense_sum

            # Only deposit if net balance is positive (saved money)
            if net_month_balance > 0:
                rollover_entry = SavingsTransaction(
                    user_id=user_id,
                    amount=net_month_balance,
                    type="deposit",
                    description=rollover_tag,
                    transaction_date=m_end,  # Last day of that month
                )
                db.add(rollover_entry)
                db.commit()

        # Move to next month
        if check_m == 12:
            check_m = 1
            check_y += 1
        else:
            check_m += 1


def calculate_savings_summary(db: Session, user_id: int) -> SavingsSummaryResponse:
    """Calculates savings statistics from the user's savings ledger.
    Formula:
    Current Savings = Initial Savings + Total Deposits - Total Withdrawals + Net Adjustments
    """
    # Auto-run monthly rollover first to ensure completed months are swept into savings
    auto_rollover_monthly_savings(db, user_id)

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
    summary = calculate_savings_summary(db, user_id)
    diff = data.target_balance - summary.current_savings

    if diff == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reported balance matches the current recorded savings balance.",
        )

    tx_date = data.transaction_date or datetime.date.today()
    record = SavingsTransaction(
        user_id=user_id,
        amount=diff,
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
    # Ensure any past months are swept into savings ledger first
    auto_rollover_monthly_savings(db, user_id)

    records = (
        db.query(SavingsTransaction)
        .filter(SavingsTransaction.user_id == user_id)
        .order_by(SavingsTransaction.transaction_date.desc(), SavingsTransaction.id.desc())
        .all()
    )
    return [SavingsTransactionResponse.from_orm_model(r) for r in records]
