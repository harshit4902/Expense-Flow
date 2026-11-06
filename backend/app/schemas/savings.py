import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict

SavingsTransactionType = Literal[
    "initial_balance",
    "deposit",
    "withdrawal",
    "balance_adjustment",
]


class SavingsTransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: int  # in paise
    amount_in_rupees: float
    type: SavingsTransactionType
    description: str
    transaction_date: datetime.date
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, record) -> "SavingsTransactionResponse":
        return cls(
            id=record.id,
            user_id=record.user_id,
            amount=record.amount,
            amount_in_rupees=round(record.amount / 100.0, 2),
            type=record.type,
            description=record.description,
            transaction_date=record.transaction_date,
            created_at=record.created_at,
        )


class SavingsInitializeRequest(BaseModel):
    amount: int = Field(..., ge=0, examples=[5000000], description="Initial savings amount in integer paise (e.g. ₹50,000 = 5000000)")
    description: Optional[str] = Field("Initial savings account balance", max_length=255)
    transaction_date: Optional[datetime.date] = Field(default_factory=datetime.date.today)


class SavingsDepositRequest(BaseModel):
    amount: int = Field(..., gt=0, examples=[500000], description="Deposit amount in integer paise (e.g. ₹5,000 = 500000)")
    description: Optional[str] = Field("Savings deposit", max_length=255)
    transaction_date: Optional[datetime.date] = Field(default_factory=datetime.date.today)


class SavingsWithdrawRequest(BaseModel):
    amount: int = Field(..., gt=0, examples=[200000], description="Withdrawal amount in integer paise (e.g. ₹2,000 = 200000)")
    description: Optional[str] = Field("Savings withdrawal", max_length=255)
    transaction_date: Optional[datetime.date] = Field(default_factory=datetime.date.today)


class SavingsBalanceAdjustmentRequest(BaseModel):
    target_balance: int = Field(..., ge=0, examples=[7500000], description="Reported or corrected current savings balance in integer paise (e.g. ₹75,000 = 7500000)")
    description: Optional[str] = Field("Manual savings balance adjustment", max_length=255)
    transaction_date: Optional[datetime.date] = Field(default_factory=datetime.date.today)


class SavingsSummaryResponse(BaseModel):
    current_savings: int  # in paise
    current_savings_in_rupees: float
    initial_savings: int  # in paise
    initial_savings_in_rupees: float
    total_deposits: int  # in paise
    total_deposits_in_rupees: float
    total_withdrawals: int  # in paise
    total_withdrawals_in_rupees: float
    net_adjustments: int  # in paise
    net_adjustments_in_rupees: float
    has_initial_balance: bool


class SavingsHistoryResponse(BaseModel):
    items: List[SavingsTransactionResponse]
    total: int

