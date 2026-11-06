import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
)
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    type: Optional[str] = Query(None, description="Filter by 'income' or 'expense'"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    start_date: Optional[datetime.date] = Query(None, description="Filter transactions from date (YYYY-MM-DD)"),
    end_date: Optional[datetime.date] = Query(None, description="Filter transactions to date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search transaction description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List transactions with filtering, searching, and pagination."""
    items, total, total_pages = transaction_service.get_transactions(
        db=db,
        user_id=current_user.id,
        type_filter=type,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a new income or expense transaction."""
    return transaction_service.create_transaction(db, current_user.id, tx_in)


@router.get("/{tx_id}", response_model=TransactionResponse)
def get_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details of a single transaction."""
    return transaction_service.get_transaction_by_id(db, tx_id, current_user.id)


@router.put("/{tx_id}", response_model=TransactionResponse)
def update_transaction(
    tx_id: int,
    tx_in: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing transaction."""
    return transaction_service.update_transaction(db, tx_id, current_user.id, tx_in)


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a transaction."""
    transaction_service.delete_transaction(db, tx_id, current_user.id)
    return None

