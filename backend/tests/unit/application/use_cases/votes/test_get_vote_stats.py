import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.votes import VoteStatsDTO
from app.application.use_cases.votes.get_vote_stats import GetVoteStatsUseCase
from app.domain.entities.enums import ReportStatus
from app.domain.entities.location import Location
from app.domain.entities.report import Report
from app.domain.exceptions.report import ReportNotFoundException


class TestGetVoteStatsUseCase:
    @pytest.fixture
    def mock_vote_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_vote_repo, mock_report_repo):
        return GetVoteStatsUseCase(
            vote_repo=mock_vote_repo, report_repo=mock_report_repo
        )

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=uuid.uuid4(),
            title="Test Stats",
            issue_type="other",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=uuid.uuid4(),
            status=ReportStatus.CONFIRMED,
        )

    async def test_get_stats_success(
        self, use_case, mock_vote_repo, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        mock_vote_repo.get_stats_by_report.return_value = {
            "confirm_count": 10,
            "dismiss_count": 2,
        }

        result = await use_case.execute(sample_report.id)

        assert isinstance(result, VoteStatsDTO)
        assert result.report_id == sample_report.id
        assert result.confirm_count == 10
        assert result.dismiss_count == 2
        assert result.current_status == ReportStatus.CONFIRMED.value

        mock_report_repo.get_by_id.assert_called_once_with(sample_report.id)
        mock_vote_repo.get_stats_by_report.assert_called_once_with(
            sample_report.id
        )

    async def test_get_stats_no_votes(
        self, use_case, mock_vote_repo, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report
        mock_vote_repo.get_stats_by_report.return_value = {}

        result = await use_case.execute(sample_report.id)

        assert result.confirm_count == 0
        assert result.dismiss_count == 0

    async def test_get_stats_report_not_found(
        self, use_case, mock_report_repo, mock_vote_repo
    ):
        mock_report_repo.get_by_id.return_value = None

        report_id = uuid.uuid4()

        with pytest.raises(ReportNotFoundException):
            await use_case.execute(report_id)

        mock_vote_repo.get_stats_by_report.assert_not_called()
