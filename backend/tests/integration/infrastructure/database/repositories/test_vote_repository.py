import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.enums import IssueType
from app.domain.entities.location import Location
from app.domain.entities.report import Report
from app.domain.entities.user import User
from app.domain.entities.vote import Vote
from app.infrastructure.database.repositories.report_repository import (
    ReportRepository,
)
from app.infrastructure.database.repositories.user_repository import (
    UserRepository,
)
from app.infrastructure.database.repositories.vote_repository import (
    VoteRepository,
)


class TestVoteRepository:
    @pytest.fixture
    async def sample_user(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        return await user_repo.save(
            User(email="voter@t.com", username="voter", password_hash="h")
        )

    @pytest.fixture
    async def sample_report(self, db_session: AsyncSession, sample_user: User):
        report_repo = ReportRepository(db_session)
        loc = Location(0, 0)
        return await report_repo.save(
            Report(
                title="Vote Target",
                issue_type=IssueType.OTHER,
                location=loc,
                user_location=loc,
                created_by_id=sample_user.id,
            )
        )

    @pytest.fixture
    def repo(self, db_session: AsyncSession):
        return VoteRepository(db_session)

    async def test_save_and_get_vote(
        self, repo: VoteRepository, sample_user: User, sample_report: Report
    ):
        vote = Vote(
            user_id=sample_user.id,
            report_id=sample_report.id,
            is_confirm=True,
            user_location=Location(longitude=0.001, latitude=0.001),
            is_verified=True,
        )

        await repo.save(vote)

        found = await repo.get_user_vote(sample_user.id, sample_report.id)

        assert found is not None
        assert found.is_confirm is True
        assert found.is_verified is True
        assert found.user_location.longitude == 0.001

    async def test_get_votes_for_reports(
        self, repo: VoteRepository, sample_user: User, db_session: AsyncSession
    ):
        report_repo = ReportRepository(db_session)
        loc = Location(0, 0)

        r1 = await report_repo.save(
            Report(
                title="R1",
                issue_type="other",
                location=loc,
                user_location=loc,
                created_by_id=sample_user.id,
            )
        )
        r2 = await report_repo.save(
            Report(
                title="R2",
                issue_type="other",
                location=loc,
                user_location=loc,
                created_by_id=sample_user.id,
            )
        )

        await repo.save(
            Vote(
                user_id=sample_user.id,
                report_id=r1.id,
                is_confirm=True,
                user_location=loc,
            )
        )

        votes_map = await repo.get_votes_for_reports(
            sample_user.id, [r1.id, r2.id]
        )

        assert len(votes_map) == 1
        assert votes_map[r1.id].is_confirm is True
        assert r2.id not in votes_map

    async def test_get_stats_by_report(
        self,
        repo: VoteRepository,
        sample_report: Report,
        db_session: AsyncSession,
    ):
        user_repo = UserRepository(db_session)
        loc = Location(0, 0)

        for i, choice in enumerate([True, True, False]):
            u = await user_repo.save(
                User(email=f"u{i}@t.com", username=f"u{i}", password_hash="h")
            )
            await repo.save(
                Vote(
                    user_id=u.id,
                    report_id=sample_report.id,
                    is_confirm=choice,
                    user_location=loc,
                )
            )

        stats = await repo.get_stats_by_report(sample_report.id)

        assert stats["confirm_count"] == 2
        assert stats["dismiss_count"] == 1

    async def test_delete_vote(
        self, repo: VoteRepository, sample_user: User, sample_report: Report
    ):
        await repo.save(
            Vote(
                user_id=sample_user.id,
                report_id=sample_report.id,
                is_confirm=True,
                user_location=Location(0, 0),
            )
        )

        await repo.delete(sample_user.id, sample_report.id)

        found = await repo.get_user_vote(sample_user.id, sample_report.id)
        assert found is None

    async def test_get_user_votes_paginated(
        self, repo: VoteRepository, sample_user: User, db_session: AsyncSession
    ):
        report_repo = ReportRepository(db_session)
        loc = Location(0, 0)

        for i in range(2):
            r = await report_repo.save(
                Report(
                    title=f"R{i}",
                    issue_type="other",
                    location=loc,
                    user_location=loc,
                    created_by_id=sample_user.id,
                )
            )
            await repo.save(
                Vote(
                    user_id=sample_user.id,
                    report_id=r.id,
                    is_confirm=True,
                    user_location=loc,
                )
            )

        votes, total = await repo.get_user_votes_paginated(
            sample_user.id, limit=1, offset=1
        )

        assert total == 2
        assert len(votes) == 1
        assert (await report_repo.get_by_id(votes[0].report_id)).title == "R0"
