from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.domain.interfaces.providers.auth_provider import IAuthProvider


class JoseAuthProvider(IAuthProvider):
    def __init__(self):
        self._pwd_context = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
            argon2__time_cost=settings.ARGON2_TIME_COST,
            argon2__memory_cost=settings.ARGON2_MEMORY_COST,
            argon2__parallelism=settings.ARGON2_PARALLELISM,
            argon2__hash_len=settings.ARGON2_HASH_LEN,
        )
        self._secret_key = settings.SECRET_KEY
        self._algorithm = settings.TOKEN_ALGORITHM
        self._pepper = settings.ARGON2_PEPPER

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password + self._pepper)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain + self._pepper, hashed)

    def create_token(self, payload: dict, expires_delta_minutes: int) -> str:
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=expires_delta_minutes
        )
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode, self._secret_key, algorithm=self._algorithm
        )
        return encoded_jwt

    def decode_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(
                token, self._secret_key, algorithms=[self._algorithm]
            )
            return payload
        except JWTError:
            return None
