from datetime import datetime, timezone

from app.application.dto.auth import VerifyEmailDTO
from app.domain.exceptions.base import BusinessRuleException
from app.domain.exceptions.user import UserNotFoundException
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class VerifyEmailUseCase:
    def __init__(
        self, user_repo: IUserRepository, token_repo: ITokenRepository
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def execute(self, dto: VerifyEmailDTO) -> None:
        # 1. Поиск токена в базе данных
        verification_token = await self.token_repo.get_verification_token(
            dto.token
        )

        # 2. Проверка существования токена
        if not verification_token:
            raise BusinessRuleException("Invalid or expired verification token")

        # 3. Проверка срока действия токена
        if verification_token.expires_at < datetime.now(timezone.utc):
            await self.token_repo.delete_verification_token(
                verification_token.token
            )
            raise BusinessRuleException("Invalid or expired verification token")

        # 4. Получение пользователя, связанного с токеном
        user = await self.user_repo.get_by_id(verification_token.user_id)
        if not user:
            raise UserNotFoundException()

        # 5. Обновление статуса пользователя
        user.is_verified = True
        await self.user_repo.save(user)

        # 6. Удаление использованного токена
        await self.token_repo.delete_verification_token(
            verification_token.token
        )
