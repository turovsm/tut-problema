import uuid
from datetime import UTC, datetime, timedelta

from app.application.dto.auth import RegisterUserDTO
from app.domain.entities.enums import UserRole
from app.domain.entities.token import VerificationToken
from app.domain.entities.user import User
from app.domain.exceptions.user import (
    EmailAlreadyRegisteredException,
    UsernameTakenException,
)
from app.domain.interfaces.providers.auth_provider import IAuthProvider
from app.domain.interfaces.providers.email_provider import IEmailProvider
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class RegisterUserUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: ITokenRepository,
        auth_provider: IAuthProvider,
        email_provider: IEmailProvider,
        verification_token_expiry_hours: int,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.auth_provider = auth_provider
        self.email_provider = email_provider
        self.token_expiry_hours = verification_token_expiry_hours

    async def execute(self, dto: RegisterUserDTO) -> User:
        # 1. Проверка уникальности email
        if await self.user_repo.get_by_email(dto.email):
            raise EmailAlreadyRegisteredException()

        # 2. Проверка уникальности username
        if await self.user_repo.get_by_username(dto.username):
            raise UsernameTakenException()

        # 3. Хеширование пароля
        hashed_password = self.auth_provider.hash_password(dto.password)

        # 4. Создание сущности пользователя
        user = User(
            email=dto.email,
            username=dto.username,
            password_hash=hashed_password,
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
        )

        # 5. Сохранение пользователя
        user = await self.user_repo.save(user)

        # 6. Генерация токена
        expires_at = datetime.now(UTC) + timedelta(
            hours=self.token_expiry_hours
        )
        verification_token = VerificationToken(
            user_id=user.id, token=uuid.uuid4(), expires_at=expires_at
        )

        await self.token_repo.save_verification_token(verification_token)

        # 7. Отправка email
        await self.email_provider.send_verification(
            email=user.email,
            name=user.username,
            token=str(verification_token.token),
        )

        return user
