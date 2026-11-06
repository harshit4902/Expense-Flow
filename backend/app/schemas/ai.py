import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, examples=["Aaj maine 20 ka samosa khaya"])


class ParsedTransaction(BaseModel):
    type: Literal["income", "expense"] = Field(..., description="'income' or 'expense'")
    amount: int = Field(..., gt=0, description="Amount in integer paise (e.g., ₹20 = 2000 paise)")
    category_name: str = Field(..., description="Matched category name, e.g. Food, Travel, Salary")
    description: str = Field(..., description="Short description of transaction, e.g. Samosa")
    date: str = Field(default_factory=lambda: datetime.date.today().isoformat(), description="YYYY-MM-DD")


class ParsedSavings(BaseModel):
    type: Literal["initial_balance", "deposit", "withdrawal", "balance_adjustment"]
    amount: int = Field(..., description="Amount in integer paise")
    description: str
    date: str = Field(default_factory=lambda: datetime.date.today().isoformat())


class LLMExtractionResult(BaseModel):
    intent: Literal["transaction", "savings", "clarification", "general_chat"]
    reply: str
    transactions: List[ParsedTransaction] = Field(default_factory=list)
    savings: Optional[ParsedSavings] = None
    requires_clarification: bool = False


class ChatResponse(BaseModel):
    reply: str
    intent: str
    recorded_transactions: List[dict] = Field(default_factory=list)
    recorded_savings: Optional[dict] = None
    requires_clarification: bool = False
