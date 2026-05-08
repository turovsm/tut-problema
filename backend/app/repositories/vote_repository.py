from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.vote import Vote
from app.repositories.base import BaseRepository


class VoteRepository(BaseRepository[Vote]):
    def __init__(self, db: AsyncSession):
        super().__init__(Vote, db)

    async def get_user_vote(
        self, user_id: UUID, report_id: UUID
    ) -> Optional[Vote]:
        result = await self.db.execute(
            select(Vote).where(
                Vote.user_id == user_id, Vote.report_id == report_id
            )
        )
        return result.scalar_one_or_none()

    async def get_report_vote_stats(self, report_id: UUID) -> dict:
        confirm_result = await self.db.execute(
            select(func.count()).where(
                Vote.report_id == report_id, Vote.is_confirm.is_(True)
            )
        )
        dismiss_result = await self.db.execute(
            select(func.count()).where(
                Vote.report_id == report_id, Vote.is_confirm.is_(False)
            )
        )
        return {
            "confirm_count": confirm_result.scalar(),
            "dismiss_count": dismiss_result.scalar(),
        }

    async def get_user_votes_paginated(
        self, user_id: UUID, limit: int, offset: int
    ):
        query = select(Vote).where(Vote.user_id == user_id)
        total = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )

        paginated_query = (
            query.order_by(Vote.created_at.desc()).offset(offset).limit(limit)
        )
        items = await self.db.execute(paginated_query)

        return items.scalars().all(), total.scalar()
