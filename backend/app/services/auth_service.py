import datetime
from pwdlib import PasswordHash
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.services.category_service import seed_default_categories

settings = get_settings()

pwd_context = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored Argon2 hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generates an Argon2 password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def register_user(db: Session, user_in: UserRegister) -> User:
    """Registers a new user and pre-seeds standard minimal categories immediately."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        hashed_password=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Immediately seed standard expense & income categories for the new user
    seed_default_categories(db, new_user.id)

    return new_user


def authenticate_user(db: Session, credentials: UserLogin) -> User:
    """Authenticates a user by email and password."""
    user = db.query(User).filter(User.email == credentials.email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Ensure default categories exist upon login as well
    seed_default_categories(db, user.id)
    return user
