from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.token import RefreshToken, VerificationToken
from app.domain.interfaces.repositories.token_repository import (
    ITokenRepository,
)
from app.infrastructure.database.models import (
    RefreshTokenModel,
    VerificationTokenModel,
)
from app.infrastructure.database.repositories.base import (
    BaseSQLAlchemyRepository,
)


class TokenRepository(
    BaseSQLAlchemyRepository[RefreshTokenModel], ITokenRepository
):
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshTokenModel, session)

    async def save_refresh_token(self, token: RefreshToken) -> None:
        query = select(RefreshTokenModel).where(
            RefreshTokenModel.jti == token.jti
        )
        res = await self._session.execute(query)
        model = res.scalar_one_or_none()

        if not model:
            model = RefreshTokenModel(
                jti=token.jti,
                user_id=token.user_id,
                expires_at=token.expires_at,
                revoked_at=token.revoked_at,
            )
            self._session.add(model)
        else:
            model.revoked_at = token.revoked_at
            model.expires_at = token.expires_at

        await self._session.flush()

    async def get_refresh_token(self, jti: str) -> RefreshToken | None:
        query = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return RefreshToken(
            jti=model.jti,
            user_id=model.user_id,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
        )

    async def save_verification_token(
        self, token: VerificationToken
    ) -> VerificationToken:
        model = VerificationTokenModel(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            created_at=token.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return token

    async def get_verification_token(
        self, token_uuid: UUID
    ) -> VerificationToken | None:
        query = select(VerificationTokenModel).where(
            VerificationTokenModel.token == token_uuid
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return VerificationToken(
            id=model.id,
            user_id=model.user_id,
            token=model.token,
            expires_at=model.expires_at,
            created_at=model.created_at,
        )

    async def delete_verification_tokens_by_user(self, user_id: UUID) -> None:
        query = delete(VerificationTokenModel).where(
            VerificationTokenModel.user_id == user_id
        )
        await self._session.execute(query)
        await self._session.flush()

    async def delete_verification_token(self, token_uuid: UUID) -> None:
        query = delete(VerificationTokenModel).where(
            VerificationTokenModel.token == token_uuid
        )
        await self._session.execute(query)
        await self._session.flush()
