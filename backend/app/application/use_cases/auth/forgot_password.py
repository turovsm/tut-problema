import uuid
from datetime import datetime, timedelta, timezone

from app.application.dto.auth import ForgotPasswordDTO
from app.domain.entities.token import VerificationToken
from app.domain.interfaces.providers.email_provider import IEmailProvider
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class ForgotPasswordUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: ITokenRepository,
        email_provider: IEmailProvider,
        reset_token_expiry_hours: int,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.email_provider = email_provider
        self.token_expiry_hours = reset_token_expiry_hours

    async def execute(self, dto: ForgotPasswordDTO) -> None:
        # 1. Поиск пользователя по email
        user = await self.user_repo.get_by_email(dto.email)

        # 2. Если пользователь не найден, просто завершаем выполнение
        if not user:
            return

        # 3. Удаляем старые токены сброса/вериифкации для этого пользователя
        await self.token_repo.delete_verification_tokens_by_user(user.id)

        # 4. Генерация токена для сброса пароля
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.token_expiry_hours
        )
        reset_token = VerificationToken(
            user_id=user.id, token=uuid.uuid4(), expires_at=expires_at
        )

        await self.token_repo.save_verification_token(reset_token)

        # 5. Отправка письма со ссылкой на восстановление
        await self.email_provider.send_password_reset(
            email=user.email, name=user.username, token=str(reset_token.token)
        )
