import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.transaction import TransactionResponse


class CategoryExpenseBreakdown(BaseModel):
    category_id: int
    category_name: str
    total_amount: int  # paise
    total_amount_in_rupees: float
    percentage: float  # e.g. 35.5%


class MonthlyTrendItem(BaseModel):
    month: int
    year: int
    month_name: str  # e.g. "Nov 2026"
    income: int  # paise
    income_in_rupees: float
    expense: int  # paise
    expense_in_rupees: float
    net_savings_or_balance: int  # income - expense (paise)
    net_savings_or_balance_in_rupees: float


class SavingsTrendItem(BaseModel):
    date: datetime.date
    running_balance: int  # paise
    running_balance_in_rupees: float
    change_type: str
    change_amount: int  # paise


class DashboardSummaryResponse(BaseModel):
    month: int
    year: int
    total_income: int  # paise
    total_income_in_rupees: float
    total_expenses: int  # paise
    total_expenses_in_rupees: float
    monthly_balance: int  # total_income - total_expenses
    monthly_balance_in_rupees: float
    current_savings: int  # paise
    current_savings_in_rupees: float
    total_budget: int  # paise
    total_budget_in_rupees: float
    budget_spent: int  # paise
    budget_spent_in_rupees: float
    budget_remaining: int  # paise
    budget_remaining_in_rupees: float
    recent_transactions: List[TransactionResponse]


class MonthlyReportResponse(BaseModel):
    month: int
    year: int
    total_income: int
    total_income_in_rupees: float
    total_expenses: int
    total_expenses_in_rupees: float
    net_savings: int  # income - expense
    net_savings_in_rupees: float
    savings_rate_percentage: float  # (net_savings / income) * 100 if income > 0 else 0.0
    category_breakdown: List[CategoryExpenseBreakdown]
    daily_spending: List[dict]

