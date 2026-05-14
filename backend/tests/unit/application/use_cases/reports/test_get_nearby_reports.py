import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.reports import NearbyReportsDTO
from app.application.use_cases.reports.get_nearby_reports import (
    GetNearbyReportsUseCase,
)
from app.domain.entities.enums import IssueType, VoteType
from app.domain.entities.location import Location
from app.domain.entities.report import Report
from app.domain.entities.vote import Vote


class TestGetNearbyReportsUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_vote_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_vote_repo):
        return GetNearbyReportsUseCase(
            report_repo=mock_report_repo, vote_repo=mock_vote_repo
        )

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=uuid.uuid4(),
            title="Nearby Issue",
            issue_type=IssueType.POTHOLE,
            location=Location(longitude=37.6, latitude=55.7),
            user_location=Location(longitude=37.6, latitude=55.7),
            created_by_id=uuid.uuid4(),
        )

    async def test_get_nearby_anonymous(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_nearby.return_value = [sample_report]

        dto = NearbyReportsDTO(
            lat=55.75, lon=37.61, radius=1000, limit=20, current_user_id=None
        )

        results = await use_case.execute(dto)

        mock_report_repo.get_nearby.assert_called_once_with(
            lat=55.75, lon=37.61, radius_meters=1000, limit=20
        )

        assert len(results) == 1
        assert results[0].id == sample_report.id
        assert results[0].current_user_vote is None

    async def test_get_nearby_with_user(
        self, use_case, mock_report_repo, mock_vote_repo, sample_report
    ):
        user_id = uuid.uuid4()
        mock_report_repo.get_nearby.return_value = [sample_report]

        mock_vote_repo.get_votes_for_reports.return_value = {
            sample_report.id: Vote(
                user_id=user_id,
                report_id=sample_report.id,
                is_confirm=False,
                user_location=Location(0, 0),
            )
        }

        dto = NearbyReportsDTO(
            lat=55.0, lon=37.0, radius=500, limit=10, current_user_id=user_id
        )

        results = await use_case.execute(dto)

        assert results[0].current_user_vote == VoteType.DISMISS

        mock_report_repo.get_nearby.assert_called_once()
        mock_vote_repo.get_votes_for_reports.assert_called_once_with(
            user_id=user_id, report_ids=[sample_report.id]
        )

    async def test_get_nearby_empty(
        self, use_case, mock_report_repo, mock_vote_repo
    ):
        mock_report_repo.get_nearby.return_value = []

        dto = NearbyReportsDTO(lat=0, lon=0, radius=100, limit=5)
        results = await use_case.execute(dto)

        assert results == []
        mock_report_repo.get_nearby.assert_called_once()
        mock_vote_repo.get_votes_for_reports.assert_not_called()
