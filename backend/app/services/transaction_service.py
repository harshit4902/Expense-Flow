import datetime
import math
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
)


def create_transaction(
    db: Session,
    user_id: int,
    tx_in: TransactionCreate,
) -> TransactionResponse:
    """Creates a new income or expense transaction."""
    # Ensure category exists and belongs to the current user
    category = (
        db.query(Category)
        .filter(Category.id == tx_in.category_id, Category.user_id == user_id)
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or does not belong to user.",
        )

    # Validate category type matches transaction type
    if category.type != tx_in.type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category.name}' is of type '{category.type}', but transaction is '{tx_in.type}'.",
        )

    new_tx = Transaction(
        user_id=user_id,
        category_id=tx_in.category_id,
        amount=tx_in.amount,
        type=tx_in.type,
        description=tx_in.description.strip(),
        transaction_date=tx_in.transaction_date,
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return TransactionResponse.from_orm_model(new_tx)


def get_transactions(
    db: Session,
    user_id: int,
    type_filter: Optional[str] = None,
    category_id: Optional[int] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[TransactionResponse], int, int]:
    """Retrieves filtered, searched, and paginated transactions for the user."""
    query = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user_id)
    )

    if type_filter:
        query = query.filter(Transaction.type == type_filter)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search.strip()}%"))

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    records = (
        query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [TransactionResponse.from_orm_model(tx) for tx in records]
    return items, total, total_pages


def get_transaction_by_id(db: Session, tx_id: int, user_id: int) -> TransactionResponse:
    """Retrieves a single transaction by ID ensuring user data isolation."""
    tx = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.id == tx_id, Transaction.user_id == user_id)
        .first()
    )
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )
    return TransactionResponse.from_orm_model(tx)


def update_transaction(
    db: Session,
    tx_id: int,
    user_id: int,
    tx_in: TransactionUpdate,
) -> TransactionResponse:
    """Updates an existing transaction."""
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == tx_id, Transaction.user_id == user_id)
        .first()
    )
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    target_type = tx_in.type if tx_in.type is not None else tx.type
    target_category_id = tx_in.category_id if tx_in.category_id is not None else tx.category_id

    # If category or type is changed, validate compatibility
    if tx_in.category_id is not None or tx_in.type is not None:
        category = (
            db.query(Category)
            .filter(Category.id == target_category_id, Category.user_id == user_id)
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or does not belong to user.",
            )
        if category.type != target_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category.name}' is '{category.type}', but transaction type is '{target_type}'.",
            )
        tx.category_id = target_category_id
        tx.type = target_type

    if tx_in.amount is not None:
        tx.amount = tx_in.amount
    if tx_in.description is not None:
        tx.description = tx_in.description.strip()
    if tx_in.transaction_date is not None:
        tx.transaction_date = tx_in.transaction_date

    db.commit()
    db.refresh(tx)
    return TransactionResponse.from_orm_model(tx)


def delete_transaction(db: Session, tx_id: int, user_id: int) -> None:
    """Deletes a transaction."""
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == tx_id, Transaction.user_id == user_id)
        .first()
    )
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )
    db.delete(tx)
    db.commit()

