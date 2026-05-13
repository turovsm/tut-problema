from datetime import UTC, datetime

from app.application.dto.auth import RefreshTokenDTO
from app.domain.interfaces.providers.auth_provider import IAuthProvider
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)


class LogoutUserUseCase:
    def __init__(
        self, token_repo: ITokenRepository, auth_provider: IAuthProvider
    ):
        self.token_repo = token_repo
        self.auth_provider = auth_provider

    async def execute(self, dto: RefreshTokenDTO) -> None:
        # 1. Декодируем токен для получения JTI
        payload = self.auth_provider.decode_token(dto.refresh_token)
        if not payload or payload.get("type") != "refresh":
            return

        jti = payload.get("jti")
        if not jti:
            return

        # 2. Ищем токен в хранилище
        stored_token = await self.token_repo.get_refresh_token(jti)

        # 3. Если токен найден и еще не отозван — отзываем его
        if stored_token and not stored_token.revoked_at:
            stored_token.revoked_at = datetime.now(UTC)
            await self.token_repo.save_refresh_token(stored_token)
