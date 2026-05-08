import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from fastapi import BackgroundTasks

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_jti,
    hash_password,
    verify_password,
)
from app.infrastructure.email import email_service
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository, token_repo: TokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def register_user(
        self, user_data: dict, background_tasks: BackgroundTasks
    ) -> dict:
        if await self.user_repo.get_by_email(user_data["email"]):
            raise ValueError("Email already registered")
        if await self.user_repo.get_by_username(user_data["username"]):
            raise ValueError("Username already taken")

        user_in = {
            "email": user_data["email"],
            "username": user_data["username"],
            "password_hash": hash_password(user_data["password"]),
            "is_active": True,
            "is_verified": False,
        }
        user = await self.user_repo.create(user_in)

        token_in = {
            "user_id": user.id,
            "token": uuid.uuid4(),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        }
        verification_token = await self.token_repo.create_verification_token(
            token_in
        )

        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            user.username,
            str(verification_token.token),
        )
        return user

    async def authenticate_user(
        self, email: str, password: str
    ) -> Tuple[dict, str, str]:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise PermissionError("Account is deactivated")

        access_token = create_access_token(str(user.id))
        jti = generate_jti()
        refresh_token = create_refresh_token(str(user.id), jti)

        await self.token_repo.create(
            {
                "jti": jti,
                "user_id": user.id,
                "expires_at": datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            }
        )

        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> Tuple[dict, str, str]:
        payload = decode_token(refresh_token, expected_type="refresh")
        if not payload:
            raise ValueError("Invalid refresh token")

        jti = payload.get("jti")
        stored_token = await self.token_repo.get_refresh_token(jti)

        if (
            not stored_token
            or stored_token.revoked_at
            or stored_token.expires_at < datetime.now(timezone.utc)
        ):
            raise ValueError("Refresh token expired or revoked")

        user = await self.user_repo.get(uuid.UUID(payload.get("sub")))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        stored_token.revoked_at = datetime.now(timezone.utc)

        access_token = create_access_token(str(user.id))
        new_jti = generate_jti()
        new_refresh_token = create_refresh_token(str(user.id), new_jti)

        await self.token_repo.create(
            {
                "jti": new_jti,
                "user_id": user.id,
                "expires_at": datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            }
        )

        await self.token_repo.db.commit()

        return user, access_token, new_refresh_token

    async def logout(self, refresh_token: str):
        payload = decode_token(refresh_token, expected_type="refresh")
        if payload:
            jti = payload.get("jti")
            stored_token = await self.token_repo.get_refresh_token(jti)
            if stored_token:
                stored_token.revoked_at = datetime.now(timezone.utc)
                await self.token_repo.db.commit()

    async def verify_email(self, token_uuid: uuid.UUID):
        token = await self.token_repo.get_verification_token(token_uuid)
        if not token or token.expires_at.replace(
            tzinfo=timezone.utc
        ) < datetime.now(timezone.utc):
            raise ValueError("Invalid or expired verification token")

        user = await self.user_repo.get(token.user_id)
        if not user:
            raise ValueError("User not found")

        user.is_verified = True
        await self.token_repo.delete_verification_token(token)
        await self.user_repo.db.commit()

    async def resend_verification(
        self, email: str, background_tasks: BackgroundTasks
    ):
        user = await self.user_repo.get_by_email(email)
        if not user or user.is_verified:
            return

        await self.token_repo.delete_verification_tokens_for_user(user.id)

        token_in = {
            "user_id": user.id,
            "token": uuid.uuid4(),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        }
        new_token = await self.token_repo.create_verification_token(token_in)

        background_tasks.add_task(
            email_service.send_verification_email,
            user.email,
            user.username,
            str(new_token.token),
        )

    async def change_password(
        self, user_id: uuid.UUID, current_pwd: str, new_pwd: str
    ):
        user = await self.user_repo.get(user_id)
        if not verify_password(current_pwd, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(new_pwd)
        await self.user_repo.db.commit()

    async def initiate_password_reset(
        self, email: str, background_tasks: BackgroundTasks
    ):
        user = await self.user_repo.get_by_email(email)
        if user:
            token_in = {
                "user_id": user.id,
                "token": uuid.uuid4(),
                "expires_at": datetime.now(timezone.utc)
                + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
            }
            reset_token = await self.token_repo.create_verification_token(
                token_in
            )

            background_tasks.add_task(
                email_service.send_password_reset_email,
                user.email,
                user.username,
                str(reset_token.token),
            )

    async def reset_password(self, token_uuid: uuid.UUID, new_password: str):
        token = await self.token_repo.get_verification_token(token_uuid)
        if not token or token.expires_at.replace(
            tzinfo=timezone.utc
        ) < datetime.now(timezone.utc):
            raise ValueError("Invalid or expired reset token")

        user = await self.user_repo.get(token.user_id)
        if not user:
            raise ValueError("User not found")

        user.password_hash = hash_password(new_password)
        await self.token_repo.delete_verification_token(token)
        await self.user_repo.db.commit()
