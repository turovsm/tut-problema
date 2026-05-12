from datetime import datetime, timezone

from app.application.dto.auth import ResetPasswordDTO
from app.domain.exceptions.base import BusinessRuleException
from app.domain.exceptions.user import UserNotFoundException
from app.domain.interfaces.providers.auth_provider import IAuthProvider
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class ResetPasswordUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: ITokenRepository,
        auth_provider: IAuthProvider,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.auth_provider = auth_provider

    async def execute(self, dto: ResetPasswordDTO) -> None:
        # 1. Поиск токена сброса в базе данных
        token_entity = await self.token_repo.get_verification_token(dto.token)

        # 2. Проверка существования и срока действия токена
        if not token_entity:
            raise BusinessRuleException("Invalid or expired reset token")

        if token_entity.expires_at < datetime.now(timezone.utc):
            # Удаляем просроченный токен
            await self.token_repo.delete_verification_token(token_entity.token)
            raise BusinessRuleException("Invalid or expired reset token")

        # 3. Поиск пользователя, которому принадлежит токен
        user = await self.user_repo.get_by_id(token_entity.user_id)
        if not user:
            raise UserNotFoundException()

        # 4. Хеширование нового пароля и обновление сущности
        user.password_hash = self.auth_provider.hash_password(dto.new_password)
        await self.user_repo.save(user)

        # 5. Удаление использованного токена
        await self.token_repo.delete_verification_token(token_entity.token)
