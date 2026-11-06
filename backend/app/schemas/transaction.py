import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.category import CategoryResponse

TransactionType = Literal["income", "expense"]


class TransactionBase(BaseModel):
    category_id: int = Field(..., examples=[1])
    # Amount stored in integer paise (₹250.50 -> 25050 paise)
    amount: int = Field(..., gt=0, examples=[25050], description="Amount in integer paise (e.g. ₹250.50 = 25050)")
    type: TransactionType = Field(..., examples=["expense"])
    description: str = Field(..., min_length=1, max_length=255, examples=["Lunch at cafe"])
    transaction_date: datetime.date = Field(default_factory=datetime.date.today, examples=["2026-11-02"])


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = Field(None, examples=[1])
    amount: Optional[int] = Field(None, gt=0, examples=[30000])
    type: Optional[TransactionType] = Field(None, examples=["expense"])
    description: Optional[str] = Field(None, min_length=1, max_length=255, examples=["Updated description"])
    transaction_date: Optional[datetime.date] = Field(None, examples=["2026-11-02"])


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    amount: int  # in paise
    amount_in_rupees: float  # convenience property
    type: TransactionType
    description: str
    transaction_date: datetime.date
    created_at: datetime.datetime
    updated_at: datetime.datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, tx) -> "TransactionResponse":
        return cls(
            id=tx.id,
            user_id=tx.user_id,
            category_id=tx.category_id,
            amount=tx.amount,
            amount_in_rupees=round(tx.amount / 100.0, 2),
            type=tx.type,
            description=tx.description,
            transaction_date=tx.transaction_date,
            created_at=tx.created_at,
            updated_at=tx.updated_at,
            category=CategoryResponse.model_validate(tx.category) if tx.category else None,
        )


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

