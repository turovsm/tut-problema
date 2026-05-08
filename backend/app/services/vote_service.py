from uuid import UUID

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import func, select

from app.core.config import settings
from app.database.models import Vote
from app.repositories.report_repository import ReportRepository
from app.repositories.vote_repository import VoteRepository
from app.schemas.vote import VoteCreate, VoteType


class VoteService:
    def __init__(
        self, vote_repo: VoteRepository, report_repo: ReportRepository
    ):
        self.vote_repo = vote_repo
        self.report_repo = report_repo

    async def get_user_votes_for_reports(
        self, user_id: UUID, report_ids: list[UUID]
    ) -> dict[UUID, Vote]:
        if not report_ids:
            return {}
        result = await self.db.execute(
            select(Vote).where(
                Vote.user_id == user_id, Vote.report_id.in_(report_ids)
            )
        )
        votes = result.scalars().all()
        return {vote.report_id: vote for vote in votes}

    async def cast_vote(
        self, user_id: UUID, report_id: UUID, vote_data: VoteCreate
    ):
        report = await self.report_repo.get(report_id)
        if not report:
            raise ValueError("Report not found")
        if report.created_by_id == user_id:
            raise PermissionError("You cannot vote on your own report")

        user_lng, user_lat = vote_data.user_location.coordinates
        user_point = Point(user_lng, user_lat)
        user_wkb = from_shape(user_point, srid=4326)

        distance_query = select(func.ST_Distance(report.location, user_wkb))
        distance = await self.report_repo.db.scalar(distance_query)

        if distance > settings.MAX_VOTE_DISTANCE_METERS:
            raise ValueError(
                f"Cannot vote. You must be within {settings.MAX_VOTE_DISTANCE_METERS} meters."
            )

        existing = await self.vote_repo.get_user_vote(user_id, report_id)
        is_confirm = vote_data.vote_type == VoteType.CONFIRM

        is_verified = False
        if vote_data.accuracy and distance <= (
            vote_data.accuracy + settings.VOTE_VERIFICATION_BUFFER_METERS
        ):
            is_verified = True

        if existing:
            existing.is_confirm = is_confirm
            existing.user_location = user_wkb
            existing.is_verified = is_verified
            await self.vote_repo.db.commit()
            return existing

        vote_dict = {
            "user_id": user_id,
            "report_id": report_id,
            "is_confirm": is_confirm,
            "user_location": user_wkb,
            "is_verified": is_verified,
        }
        vote = await self.vote_repo.create(vote_dict)
        await self.vote_repo.db.commit()
        return vote

    async def remove_vote(self, user_id: UUID, report_id: UUID):
        vote = await self.vote_repo.get_user_vote(user_id, report_id)
        if not vote:
            raise ValueError("Vote not found")
        await self.vote_repo.delete(vote.id)
        await self.vote_repo.db.commit()
