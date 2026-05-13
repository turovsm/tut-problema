import uuid
from datetime import UTC, datetime, timedelta

from app.application.dto.auth import ResendVerificationDTO
from app.domain.entities.token import VerificationToken
from app.domain.interfaces.providers.email_provider import IEmailProvider
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class ResendVerificationUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: ITokenRepository,
        email_provider: IEmailProvider,
        verification_token_expiry_hours: int,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.email_provider = email_provider
        self.token_expiry_hours = verification_token_expiry_hours

    async def execute(self, dto: ResendVerificationDTO) -> None:
        # 1. Поиск пользователя по email
        user = await self.user_repo.get_by_email(dto.email)

        # 2. Если пользователь не найден или уже подтвержден, просто выходим
        if not user or user.is_verified:
            return

        # 3. Удаляем все существующие токены верификации этого пользователя
        await self.token_repo.delete_verification_tokens_by_user(user.id)

        # 4. Генерация нового токена
        expires_at = datetime.now(UTC) + timedelta(
            hours=self.token_expiry_hours
        )
        new_token = VerificationToken(
            user_id=user.id, token=uuid.uuid4(), expires_at=expires_at
        )

        await self.token_repo.save_verification_token(new_token)

        # 5. Отправка нового письма
        await self.email_provider.send_verification(
            email=user.email, name=user.username, token=str(new_token.token)
        )
