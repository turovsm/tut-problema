from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.location import Location
from app.domain.entities.vote import Vote
from app.domain.interfaces.repositories.vote_repository import IVoteRepository
from app.infrastructure.database.models import VoteModel
from app.infrastructure.database.repositories.base import (
    BaseSQLAlchemyRepository,
)


class VoteRepository(BaseSQLAlchemyRepository[VoteModel], IVoteRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(VoteModel, session)

    def _to_domain(self, model: VoteModel) -> Vote:
        shape = to_shape(model.user_location)
        return Vote(
            id=model.id,
            user_id=model.user_id,
            report_id=model.report_id,
            is_confirm=model.is_confirm,
            user_location=Location(longitude=shape.x, latitude=shape.y),
            is_verified=model.is_verified,
            created_at=model.created_at,
        )

    async def get_user_vote(
        self, user_id: UUID, report_id: UUID
    ) -> Vote | None:
        query = select(self._model).where(
            and_(
                self._model.user_id == user_id,
                self._model.report_id == report_id,
            )
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_votes_for_reports(
        self, user_id: UUID, report_ids: list[UUID]
    ) -> dict[UUID, Vote]:
        if not report_ids:
            return {}

        query = select(self._model).where(
            and_(
                self._model.user_id == user_id,
                self._model.report_id.in_(report_ids),
            )
        )
        result = await self._session.execute(query)
        models = result.scalars().all()

        return {m.report_id: self._to_domain(m) for m in models}

    async def save(self, vote: Vote) -> Vote:
        query = select(self._model).where(
            and_(
                self._model.user_id == vote.user_id,
                self._model.report_id == vote.report_id,
            )
        )
        res = await self._session.execute(query)
        model = res.scalar_one_or_none()

        loc_wkb = from_shape(
            Point(vote.user_location.longitude, vote.user_location.latitude),
            srid=4326,
        )

        if not model:
            model = VoteModel(
                id=vote.id,
                user_id=vote.user_id,
                report_id=vote.report_id,
                is_confirm=vote.is_confirm,
                user_location=loc_wkb,
                is_verified=vote.is_verified,
                created_at=vote.created_at,
            )
        else:
            model.is_confirm = vote.is_confirm
            model.user_location = loc_wkb
            model.is_verified = vote.is_verified

        model = await self._save(model)
        return self._to_domain(model)

    async def delete(self, user_id: UUID, report_id: UUID) -> None:
        query = select(self._model).where(
            and_(
                self._model.user_id == user_id,
                self._model.report_id == report_id,
            )
        )
        res = await self._session.execute(query)
        model = res.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_stats_by_report(self, report_id: UUID) -> dict[str, int]:
        query = (
            select(self._model.is_confirm, func.count(self._model.id))
            .where(self._model.report_id == report_id)
            .group_by(self._model.is_confirm)
        )

        result = await self._session.execute(query)
        rows = result.all()

        stats = {"confirm_count": 0, "dismiss_count": 0}
        for is_confirm, count in rows:
            if is_confirm:
                stats["confirm_count"] = count
            else:
                stats["dismiss_count"] = count
        return stats

    async def get_user_votes_paginated(
        self, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[Vote], int]:
        query = select(self._model).where(self._model.user_id == user_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self._session.execute(count_query)

        query = (
            query.order_by(self._model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(query)

        return [
            self._to_domain(m) for m in result.scalars().all()
        ], total.scalar() or 0
