from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.token import RefreshToken, VerificationToken


class ITokenRepository(ABC):
    @abstractmethod
    async def save_refresh_token(self, token: RefreshToken) -> None: ...

    @abstractmethod
    async def get_refresh_token(self, jti: str) -> RefreshToken | None: ...

    @abstractmethod
    async def save_verification_token(
        self, token: VerificationToken
    ) -> VerificationToken: ...

    @abstractmethod
    async def get_verification_token(
        self, token_uuid: UUID
    ) -> VerificationToken | None: ...

    @abstractmethod
    async def delete_verification_tokens_by_user(
        self, user_id: UUID
    ) -> None: ...

    @abstractmethod
    async def delete_verification_token(self, token_uuid: UUID) -> None: ...
