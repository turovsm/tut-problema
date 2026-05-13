import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.enums import IssueType, ReportStatus
from app.domain.entities.location import Location
from app.domain.entities.report import Report, ReportPhoto
from app.domain.entities.user import User
from app.infrastructure.database.repositories.report_repository import (
    ReportRepository,
)
from app.infrastructure.database.repositories.user_repository import (
    UserRepository,
)


class TestReportRepository:
    @pytest.fixture
    async def sample_user(self, db_session: AsyncSession):
        user_repo = UserRepository(db_session)
        user = User(
            email="author@test.com", username="author", password_hash="h"
        )
        return await user_repo.save(user)

    @pytest.fixture
    def repo(self, db_session: AsyncSession):
        return ReportRepository(db_session)

    async def test_save_and_get_by_id(
        self, repo: ReportRepository, sample_user: User
    ):
        report_id = uuid.uuid4()
        new_report = Report(
            id=report_id,
            title="Pothole on Broadway",
            issue_type=IssueType.POTHOLE,
            location=Location(longitude=37.61, latitude=55.75),
            user_location=Location(longitude=37.611, latitude=55.751),
            created_by_id=sample_user.id,
            description="Deep hole",
        )

        await repo.save(new_report)

        found = await repo.get_by_id(report_id)

        assert found is not None
        assert found.title == "Pothole on Broadway"
        assert found.location.longitude == 37.61
        assert found.location.latitude == 55.75
        assert found.created_by is not None
        assert found.created_by.id == sample_user.id

    async def test_get_nearby_reports(
        self, repo: ReportRepository, sample_user: User
    ):
        center = Location(0.0, 0.0)
        await repo.save(
            Report(
                title="Center",
                issue_type="other",
                location=center,
                user_location=center,
                created_by_id=sample_user.id,
            )
        )

        nearby = Location(0.005, 0.005)
        await repo.save(
            Report(
                title="Nearby",
                issue_type="other",
                location=nearby,
                user_location=nearby,
                created_by_id=sample_user.id,
            )
        )

        far = Location(1.0, 1.0)
        await repo.save(
            Report(
                title="Far",
                issue_type="other",
                location=far,
                user_location=far,
                created_by_id=sample_user.id,
            )
        )

        results = await repo.get_nearby(
            lat=0.0, lon=0.0, radius_meters=1000, limit=10
        )

        assert len(results) == 2
        titles = [r.title for r in results]
        assert "Center" in titles
        assert "Nearby" in titles
        assert "Far" not in titles

    async def test_add_get_delete_photo(
        self, repo: ReportRepository, sample_user: User
    ):
        report = Report(
            title="T",
            issue_type="other",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=sample_user.id,
        )
        await repo.save(report)

        photo = ReportPhoto(
            report_id=report.id,
            file_name="test.jpg",
            file_path="/tmp/test.jpg",
        )
        await repo.add_photo(photo)

        found_photo = await repo.get_photo_by_id(photo.id)
        assert found_photo is not None
        assert found_photo.file_name == "test.jpg"
        assert found_photo.report_id == report.id

        found_report = await repo.get_by_id(report.id)
        assert len(found_report.photos) == 1
        assert found_report.photos[0].file_name == "test.jpg"

        await repo.delete_photo(photo.id)

        after_delete = await repo.get_by_id(report.id)
        assert len(after_delete.photos) == 0

    async def test_get_list_filtering(
        self, repo: ReportRepository, sample_user: User
    ):
        loc = Location(0, 0)
        for i in range(3):
            await repo.save(
                Report(
                    title=f"Snow {i}",
                    issue_type=IssueType.SNOW,
                    location=loc,
                    user_location=loc,
                    created_by_id=sample_user.id,
                    status=ReportStatus.PENDING,
                )
            )

        await repo.save(
            Report(
                title="Pothole 1",
                issue_type=IssueType.POTHOLE,
                location=loc,
                user_location=loc,
                created_by_id=sample_user.id,
                status=ReportStatus.CONFIRMED,
            )
        )

        reports, total = await repo.get_list(
            issue_type=IssueType.SNOW, limit=2, offset=2
        )
        assert total == 3
        assert len(reports) == 1
        assert reports[0].title == "Snow 0"
        assert reports[0].issue_type == IssueType.SNOW

        reports, total = await repo.get_list(status=ReportStatus.CONFIRMED)
        assert total == 1
        assert reports[0].status == ReportStatus.CONFIRMED

    async def test_delete_report(
        self, repo: ReportRepository, sample_user: User
    ):
        report = Report(
            title="To Delete",
            issue_type="other",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=sample_user.id,
        )
        await repo.save(report)
        photo = ReportPhoto(
            report_id=report.id, file_name="casc.jpg", file_path="/tmp/casc"
        )
        await repo.add_photo(photo)

        await repo.delete(report.id)

        assert await repo.get_by_id(report.id) is None
        assert await repo.get_photo_by_id(photo.id) is None

    async def test_get_by_user(
        self,
        repo: ReportRepository,
        sample_user: User,
        db_session: AsyncSession,
    ):
        user_repo = UserRepository(db_session)
        other_user = await user_repo.save(
            User(email="other@t.com", username="other", password_hash="h")
        )

        loc = Location(0, 0)
        await repo.save(
            Report(
                title="My Report",
                issue_type="other",
                location=loc,
                user_location=loc,
                created_by_id=sample_user.id,
            )
        )
        await repo.save(
            Report(
                title="Other Report",
                issue_type="other",
                location=loc,
                user_location=loc,
                created_by_id=other_user.id,
            )
        )

        reports, total = await repo.get_by_user(
            sample_user.id, limit=10, offset=0
        )

        assert total == 1
        assert len(reports) == 1
        assert reports[0].title == "My Report"
        assert reports[0].created_by_id == sample_user.id
