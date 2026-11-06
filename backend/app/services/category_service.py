from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

DEFAULT_EXPENSE_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "Healthcare",
    "Education",
    "Entertainment",
    "Groceries",
    "Rent",
    "Other",
]

DEFAULT_INCOME_CATEGORIES = [
    "Salary",
    "Freelancing",
    "Business",
    "Investment",
    "Gift",
    "Other",
]


def seed_default_categories(db: Session, user_id: int) -> None:
    """Seeds default income and expense categories for a user if they have none."""
    existing_count = db.query(Category).filter(Category.user_id == user_id).count()
    if existing_count > 0:
        return

    categories = []
    for name in DEFAULT_EXPENSE_CATEGORIES:
        categories.append(Category(user_id=user_id, name=name, type="expense"))
    for name in DEFAULT_INCOME_CATEGORIES:
        categories.append(Category(user_id=user_id, name=name, type="income"))

    db.add_all(categories)
    db.commit()


def get_categories(
    db: Session,
    user_id: int,
    type_filter: Optional[str] = None,
) -> List[Category]:
    """Retrieves all categories for the user, creating defaults if not yet seeded."""
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
    # Check duplicate for the same user and type
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

    # Check duplicate
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

    # Check if category has transactions
    if category.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category because it has associated transactions.",
        )

    # Check if category has budgets
    if category.budgets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category because it has associated budgets.",
        )

    db.delete(category)
    db.commit()

