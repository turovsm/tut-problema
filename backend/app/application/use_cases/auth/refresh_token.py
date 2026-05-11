import uuid
from datetime import datetime, timedelta, timezone

from app.application.dto.auth import AuthResultDTO, RefreshTokenDTO
from app.domain.entities.token import RefreshToken
from app.domain.exceptions.base import UnauthorizedException
from app.domain.exceptions.user import UserInactiveException
from app.domain.interfaces.providers.auth_provider import IAuthProvider
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class RefreshTokenUseCase:
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

    async def execute(self, dto: RefreshTokenDTO) -> AuthResultDTO:
        # 1. Декодирование и базовая проверка JWT
        payload = self.auth_provider.decode_token(dto.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        # 2. Извлечение JTI и идентификатора пользователя
        jti = payload.get("jti")
        user_id_str = payload.get("sub")
        if not jti or not user_id_str:
            raise UnauthorizedException("Invalid token payload")

        # 3. Проверка наличия токена в БД
        stored_token = await self.token_repo.get_refresh_token(jti)

        if not stored_token:
            raise UnauthorizedException("Refresh token not found")

        if stored_token.revoked_at:
            raise UnauthorizedException("Refresh token has been revoked")

        if stored_token.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedException("Refresh token expired")

        # 4. Проверка пользователя
        user_id = uuid.UUID(user_id_str)
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise UnauthorizedException("User not found")
        if not user.is_active:
            raise UserInactiveException()

        # 5. Отзыв текущего токена
        stored_token.revoked_at = datetime.now(timezone.utc)
        await self.token_repo.save_refresh_token(stored_token)

        # 6. Генерация новой пары токенов
        new_access_token = self.auth_provider.create_token(
            payload={"sub": str(user.id), "type": "access"},
            expires_delta_minutes=self.access_expiry_min,
        )

        new_jti = str(uuid.uuid4())
        new_refresh_token = self.auth_provider.create_token(
            payload={"sub": str(user.id), "type": "refresh", "jti": new_jti},
            expires_delta_minutes=self.refresh_expiry_days * 24 * 60,
        )

        # 7. Сохранение нового Refresh токена
        new_expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_expiry_days
        )
        new_token_entity = RefreshToken(
            jti=new_jti, user_id=user.id, expires_at=new_expires_at
        )
        await self.token_repo.save_refresh_token(new_token_entity)

        # 8. Возврат результата
        return AuthResultDTO(
            user=user,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            access_max_age=self.access_expiry_min * 60,
            refresh_max_age=self.refresh_expiry_days * 24 * 60 * 60,
        )
