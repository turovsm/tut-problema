from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from app.core.config import settings
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=settings.ARGON2_TIME_COST,
    argon2__memory_cost=settings.ARGON2_MEMORY_COST,
    argon2__parallelism=settings.ARGON2_PARALLELISM,
    argon2__hash_len=settings.ARGON2_HASH_LEN,
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password + settings.ARGON2_PEPPER)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password + settings.ARGON2_PEPPER, hashed_password)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.TOKEN_ALGORITHM)


def create_refresh_token(user_id: str, jti: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire, "type": "refresh", "jti": jti}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.TOKEN_ALGORITHM)


def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.TOKEN_ALGORITHM])
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


def generate_jti() -> str:
    return str(uuid4())
