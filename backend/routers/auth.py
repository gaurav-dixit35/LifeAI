from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.db import AsyncSessionLocal, get_db
from models.user_model import User
from schemas.auth_schema import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleAuthRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)


router = APIRouter()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(subject: str, *, expires_minutes: int | None = None) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def ensure_default_admin() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        user = result.scalar_one_or_none()
        hashed_password = hash_password(settings.ADMIN_PASSWORD)

        if user is None:
            db.add(
                User(
                    email=settings.ADMIN_EMAIL,
                    name="LifeAI Admin",
                    hashed_password=hashed_password,
                    is_admin=True,
                    is_active=True,
                )
            )
        else:
            user.is_admin = True
            user.is_active = True
            user.name = user.name or "LifeAI Admin"
            user.hashed_password = hashed_password
        await db.commit()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> Token:
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return Token(
        access_token=create_access_token(user.email),
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    expires_minutes = (
        settings.REMEMBER_ME_EXPIRE_MINUTES
        if credentials.remember_me
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    return Token(
        access_token=create_access_token(user.email, expires_minutes=expires_minutes),
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    preview_reset_url: str | None = None

    if user is not None:
        raw_token = secrets.token_urlsafe(32)
        user.reset_token = hash_reset_token(raw_token)
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        await db.commit()
        if settings.DEBUG:
            preview_reset_url = (
                f"{settings.FRONTEND_APP_URL}/reset-password?token={raw_token}"
            )

    return ForgotPasswordResponse(
        message="If that email exists, a reset link is now ready.",
        preview_reset_url=preview_reset_url,
    )


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(User).where(User.reset_token == hash_reset_token(payload.token))
    )
    user = result.scalar_one_or_none()

    expires_at = user.reset_token_expires_at if user else None
    if user is None or expires_at is None or expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This password reset link is invalid or expired")

    user.hashed_password = hash_password(payload.password)
    user.reset_token = None
    user.reset_token_expires_at = None
    await db.commit()
    return {"message": "Password updated successfully"}


@router.post("/google", response_model=Token)
async def google_sign_in(
    payload: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Google sign-in is not configured")

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=8.0)) as client:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.credential},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Unable to verify Google sign-in")

    data = response.json()
    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Google client mismatch")
    if data.get("email_verified") not in {"true", True}:
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    email = str(data.get("email") or "").strip().lower()
    name = str(data.get("name") or email.split("@")[0] or "Google User").strip()
    google_sub = str(data.get("sub") or "").strip()
    if not email or not google_sub:
        raise HTTPException(status_code=401, detail="Google sign-in did not return a valid account")

    result = await db.execute(
        select(User).where((User.google_sub == google_sub) | (User.email == email))
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            name=name,
            hashed_password=hash_password(secrets.token_urlsafe(24)),
            google_sub=google_sub,
        )
        db.add(user)
    else:
        user.google_sub = google_sub
        if not user.name:
            user.name = name
    await db.commit()
    await db.refresh(user)

    expires_minutes = (
        settings.REMEMBER_ME_EXPIRE_MINUTES
        if payload.remember_me
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return Token(
        access_token=create_access_token(user.email, expires_minutes=expires_minutes),
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
