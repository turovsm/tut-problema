import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.votes import CastVoteDTO
from app.application.use_cases.votes.cast_vote import CastVoteUseCase
from app.domain.entities.enums import VoteType
from app.domain.entities.location import Location
from app.domain.entities.report import Report
from app.domain.exceptions.vote import (
    SelfVotingException,
    VoteDistanceException,
)


class TestCastVoteUseCase:
    @pytest.fixture
    def mock_vote_repo(self):
        repo = AsyncMock()
        repo.save.side_effect = lambda x: x
        return repo

    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vote_repo, mock_report_repo):
        return CastVoteUseCase(
            vote_repo=mock_vote_repo,
            report_repo=mock_report_repo,
            max_vote_distance_meters=1000,
            verification_buffer_meters=50,
            earth_radius=6371000.0,
        )

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=uuid.uuid4(),
            title="Test Issue",
            issue_type="pothole",
            location=Location(0.0, 0.0),
            user_location=Location(0.0, 0.0),
            created_by_id=uuid.uuid4(),
        )

    async def test_cast_vote_verified(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = CastVoteDTO(
            user_id=uuid.uuid4(),
            report_id=sample_report.id,
            vote_type=VoteType.CONFIRM,
            user_location_lng=0.00027,
            user_location_lat=0.0,
            accuracy=10.0,
        )

        result = await use_case.execute(dto)

        assert result.is_verified is True
        assert result.is_confirm is True

    async def test_cast_vote_not_verified(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = CastVoteDTO(
            user_id=uuid.uuid4(),
            report_id=sample_report.id,
            vote_type=VoteType.CONFIRM,
            user_location_lng=0.0018,
            user_location_lat=0.0,
            accuracy=10.0,
        )

        result = await use_case.execute(dto)

        assert result.is_verified is False

    async def test_cast_vote_self_voting(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = CastVoteDTO(
            user_id=sample_report.created_by_id,
            report_id=sample_report.id,
            vote_type=VoteType.CONFIRM,
            user_location_lng=0.0,
            user_location_lat=0.0,
        )

        with pytest.raises(SelfVotingException):
            await use_case.execute(dto)

    async def test_cast_vote_too_far(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = CastVoteDTO(
            user_id=uuid.uuid4(),
            report_id=sample_report.id,
            vote_type=VoteType.CONFIRM,
            user_location_lng=0.1,
            user_location_lat=0.0,
        )

        with pytest.raises(VoteDistanceException):
            await use_case.execute(dto)
