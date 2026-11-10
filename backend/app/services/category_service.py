from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

# Minimal, clean standard categories
DEFAULT_EXPENSE_CATEGORIES = [
    "Food",          # Meals, dining, cafe, snacks
    "Travel",        # Transport, commute, fuel, cabs, metro, bus
    "Shopping",      # Clothes, electronics, items
    "Bills",         # Electricity, water, wifi, recharges, utilities
    "Rent",          # Housing, room, flat rent
    "Groceries",     # Daily essentials, kitchen, supermarket
    "Healthcare",    # Medicines, doctor, hospital
    "Entertainment", # Movies, outings, games, parties
    "Education",     # Courses, books, fees
    "Other",         # Miscellaneous expenses
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary",        # Job salary, wages, stipend
    "Freelancing",   # Client gigs, projects, contracts
    "Business",      # Business revenue, store profits
    "Investment",    # Stocks, mutual funds, interest, dividends
    "Gift",          # Received from friends/relatives/roommates
    "Other",         # Other income
]


def seed_default_categories(db: Session, user_id: int) -> None:
    """Ensures that the minimal standard categories exist for the user,
    without overwriting or duplicating any custom categories the user already created.
    """
    existing_cats = db.query(Category).filter(Category.user_id == user_id).all()
    existing_expense_names = {c.name.lower() for c in existing_cats if c.type == "expense"}
    existing_income_names = {c.name.lower() for c in existing_cats if c.type == "income"}

    new_categories = []
    for name in DEFAULT_EXPENSE_CATEGORIES:
        if name.lower() not in existing_expense_names:
            new_categories.append(Category(user_id=user_id, name=name, type="expense"))
            existing_expense_names.add(name.lower())

    for name in DEFAULT_INCOME_CATEGORIES:
        if name.lower() not in existing_income_names:
            new_categories.append(Category(user_id=user_id, name=name, type="income"))
            existing_income_names.add(name.lower())

    if new_categories:
        db.add_all(new_categories)
        db.commit()


def get_categories(
    db: Session,
    user_id: int,
    type_filter: Optional[str] = None,
) -> List[Category]:
    """Retrieves all categories for the user, auto-seeding standard categories if missing."""
    seed_default_categories(db, user_id)
    query = db.query(Category).filter(Category.user_id == user_id)
    if type_filter:
        query = query.filter(Category.type == type_filter)
    return query.order_by(Category.name.asc()).all()


def get_category_by_id(db: Session, category_id: int, user_id: int) -> Category:
    """Retrieves a specific category belonging to the user."""
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user_id)
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )
    return category


def create_category(db: Session, user_id: int, category_in: CategoryCreate) -> Category:
    """Creates a new custom category for the user."""
    clean_name = category_in.name.strip()
    existing = (
        db.query(Category)
        .filter(
            Category.user_id == user_id,
            Category.name.ilike(clean_name),
            Category.type == category_in.type,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{clean_name}' for type '{category_in.type}' already exists.",
        )

    category = Category(
        user_id=user_id,
        name=clean_name,
        type=category_in.type,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session,
    category_id: int,
    user_id: int,
    category_in: CategoryUpdate,
) -> Category:
    """Updates an existing category name."""
    category = get_category_by_id(db, category_id, user_id)
    clean_name = category_in.name.strip()

    existing = (
        db.query(Category)
        .filter(
            Category.user_id == user_id,
            Category.name.ilike(clean_name),
            Category.type == category.type,
            Category.id != category_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{clean_name}' already exists.",
        )

    category.name = clean_name
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int, user_id: int) -> None:
    """Deletes a category if not in use by transactions or budgets."""
    category = get_category_by_id(db, category_id, user_id)

    if category.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category because it has associated transactions.",
        )

    if category.budgets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category because it has associated budgets.",
        )

    db.delete(category)
    db.commit()
