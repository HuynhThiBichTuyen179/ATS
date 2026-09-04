from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.id_generator import generate_business_id
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.enums import UserRole, UserStatus
from app.models.user import User


def register_candidate(db: Session, full_name: str, email: str, password: str, phone: str | None) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "EMAIL_ALREADY_REGISTERED")

    user = User(
        business_id=generate_business_id(db, "user"),
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=UserRole.CANDIDATE,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ACCOUNT_NOT_ACTIVE")
    return user


def issue_tokens(db: Session, user: User) -> dict:
    access_token = create_access_token(user.business_id, user.role.value)
    raw_refresh, refresh_hash, expires_at = generate_refresh_token()
    user.refresh_token_hash = refresh_hash
    user.refresh_token_expires_at = expires_at
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, raw_refresh_token: str) -> dict:
    token_hash = hash_refresh_token(raw_refresh_token)
    user = db.query(User).filter(User.refresh_token_hash == token_hash).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "INVALID_REFRESH_TOKEN")
    expires_at = user.refresh_token_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at is None or expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "REFRESH_TOKEN_EXPIRED")

    access_token = create_access_token(user.business_id, user.role.value)
    return {"access_token": access_token, "token_type": "bearer"}
