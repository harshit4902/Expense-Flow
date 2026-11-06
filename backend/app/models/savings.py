import datetime
from sqlalchemy import String, Integer, BigInteger, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SavingsTransaction(Base):
    __tablename__ = "savings_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Stored strictly as integer paise
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # type: 'initial_balance', 'deposit', 'withdrawal', 'balance_adjustment'
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    transaction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="savings_transactions")

