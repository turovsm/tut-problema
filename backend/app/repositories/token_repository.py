from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.token import RefreshToken, VerificationToken
from app.repositories.base import BaseRepository


class TokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(RefreshToken, db)

    async def get_refresh_token(self, jti: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def get_verification_token(
        self, token: UUID
    ) -> Optional[VerificationToken]:
        result = await self.db.execute(
            select(VerificationToken).where(VerificationToken.token == token)
        )
        return result.scalar_one_or_none()

    async def create_verification_token(
        self, obj_in: dict
    ) -> VerificationToken:
        db_obj = VerificationToken(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def delete_verification_tokens_for_user(self, user_id: UUID):
        await self.db.execute(
            delete(VerificationToken).where(
                VerificationToken.user_id == user_id
            )
        )
        await self.db.flush()

    async def delete_verification_token(self, token: VerificationToken):
        await self.db.delete(token)
        await self.db.flush()
