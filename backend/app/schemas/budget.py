import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.category import CategoryResponse


class BudgetBase(BaseModel):
    category_id: Optional[int] = Field(None, examples=[1], description="Leave empty/null for overall monthly budget, or set category_id for category-specific budget")
    # Budget amount in integer paise (e.g. ₹15,000 = 1500000 paise)
    amount: int = Field(..., gt=0, examples=[1500000], description="Budget limit in integer paise")
    month: int = Field(..., ge=1, le=12, examples=[11])
    year: int = Field(..., ge=2000, le=2100, examples=[2026])


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    amount: Optional[int] = Field(None, gt=0, examples=[2000000])
    category_id: Optional[int] = Field(None)


class BudgetResponse(BaseModel):
    id: int
    user_id: int
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    is_overall: bool
    amount: int  # in paise
    amount_in_rupees: float
    spent: int  # in paise
    spent_in_rupees: float
    remaining: int  # max(0, amount - spent)
    remaining_in_rupees: float
    percentage_used: float  # e.g. 85.5%
    warning_status: str  # "normal", "warning" (>=80%), "exceeded" (>100%)
    month: int
    year: int
    created_at: datetime.datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetSummary(BaseModel):
    month: int
    year: int
    overall_budget: Optional[BudgetResponse] = None
    category_budgets: List[BudgetResponse]
    total_budget_amount: int
    total_budget_amount_in_rupees: float
    total_spent: int
    total_spent_in_rupees: float
    total_remaining: int
    total_remaining_in_rupees: float
    has_exceeded_any: bool
    has_warning_any: bool

