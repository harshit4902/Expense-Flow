import datetime
from typing import Optional
from sqlalchemy import Integer, BigInteger, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # category_id is nullable: None represents overall monthly budget, non-null represents category-specific budget
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    # Budget amount in integer paise
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 12
    year: Mapped[int] = mapped_column(Integer, nullable=False)   # e.g. 2026
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Unique constraint per user, month, year and category (SQLite handles NULL in unique indexes specifically;
    # we enforce unique constraint on user_id, month, year, category_id)
    __table_args__ = (
        UniqueConstraint("user_id", "month", "year", "category_id", name="uq_user_budget_period_category"),
    )

    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

