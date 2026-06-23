import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.token_store import TokenStore
from app.models.user import User


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _generate_jti() -> str:
    return uuid.uuid4().hex


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access", "jti": _generate_jti()})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> tuple[str, str]:
    jti = _generate_jti()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def store_refresh_jti(db: AsyncSession, jti: str, user_email: str) -> None:
    db.add(TokenStore(jti=jti, user_email=user_email))
    await db.commit()


async def is_jti_used(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(
        select(TokenStore).where(TokenStore.jti == jti, TokenStore.is_used.is_(True))
    )
    return result.scalar_one_or_none() is not None


async def mark_jti_used(db: AsyncSession, jti: str) -> None:
    result = await db.execute(select(TokenStore).where(TokenStore.jti == jti))
    record = result.scalar_one_or_none()
    if record:
        record.is_used = True
        await db.commit()


async def invalidate_all_user_tokens(db: AsyncSession, user_email: str) -> None:
    result = await db.execute(
        select(TokenStore).where(
            TokenStore.user_email == user_email, TokenStore.is_used.is_(False)
        )
    )
    for record in result.scalars().all():
        record.is_used = True
    await db.commit()
