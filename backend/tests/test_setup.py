import datetime
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.savings import SavingsTransaction


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "ExpenseFlow"


def test_models_setup(db_session):
    # Test User creation
    user = User(
        name="Test User",
        email="test@example.com",
        hashed_password="fakehashedpassword",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.name == "Test User"

    # Test Category creation
    category = Category(
        user_id=user.id,
        name="Food",
        type="expense",
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    assert category.id is not None
    assert category.name == "Food"

    # Test Transaction creation with integer paise (₹250.50 -> 25050 paise)
    tx = Transaction(
        user_id=user.id,
        category_id=category.id,
        amount=25050,
        type="expense",
        description="Lunch at cafe",
        transaction_date=datetime.date.today(),
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)

    assert tx.id is not None
    assert tx.amount == 25050
    assert tx.category.name == "Food"

    # Test Budget creation
    budget = Budget(
        user_id=user.id,
        category_id=category.id,
        amount=500000,  # ₹5,000.00
        month=11,
        year=2026,
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)

    assert budget.id is not None
    assert budget.amount == 500000

    # Test SavingsTransaction creation
    savings = SavingsTransaction(
        user_id=user.id,
        amount=5000000,  # ₹50,000.00
        type="initial_balance",
        description="Initial savings account balance",
        transaction_date=datetime.date.today(),
    )
    db_session.add(savings)
    db_session.commit()
    db_session.refresh(savings)

    assert savings.id is not None
    assert savings.amount == 5000000

