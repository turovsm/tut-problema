import uuid
from datetime import datetime, timedelta, timezone

from app.application.dto.auth import AuthResultDTO, LoginDTO
from app.domain.entities.token import RefreshToken
from app.domain.exceptions.base import UnauthorizedException
from app.domain.exceptions.user import (
    EmailNotVerifiedException,
    UserInactiveException,
)
from app.domain.interfaces.providers.auth_provider import IAuthProvider
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class LoginUserUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: ITokenRepository,
        auth_provider: IAuthProvider,
        access_token_expiry_minutes: int,
        refresh_token_expiry_days: int,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.auth_provider = auth_provider
        self.access_expiry_min = access_token_expiry_minutes
        self.refresh_expiry_days = refresh_token_expiry_days

    async def execute(self, dto: LoginDTO) -> AuthResultDTO:
        # 1. Поиск пользователя по Email
        user = await self.user_repo.get_by_email(dto.email)

        # 2. Проверка существования и пароля
        if not user or not self.auth_provider.verify_password(
            dto.password, user.password_hash
        ):
            raise UnauthorizedException("Invalid email or password")

        # 3. Проверка статуса (is_active)
        if not user.is_active:
            raise UserInactiveException()

        # 4. Подготовка Access токена
        access_token = self.auth_provider.create_token(
            payload={"sub": str(user.id), "type": "access"},
            expires_delta_minutes=self.access_expiry_min,
        )

        # 5. Генерация Refresh токена
        jti = str(uuid.uuid4())
        refresh_token = self.auth_provider.create_token(
            payload={"sub": str(user.id), "type": "refresh", "jti": jti},
            expires_delta_minutes=self.refresh_expiry_days * 24 * 60,
        )

        # 6. Сохранение Refresh токена
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_expiry_days
        )
        refresh_token_entity = RefreshToken(
            jti=jti, user_id=user.id, expires_at=expires_at
        )

        await self.token_repo.save_refresh_token(refresh_token_entity)

        # 7. Возврат DTO
        return AuthResultDTO(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            access_max_age=self.access_expiry_min * 60,
            refresh_max_age=self.refresh_expiry_days * 24 * 60 * 60,
        )
