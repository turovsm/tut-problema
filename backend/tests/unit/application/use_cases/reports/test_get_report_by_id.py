import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.reports.get_report_by_id import (
    GetReportByIdUseCase,
)
from app.domain.entities.enums import IssueType, VoteType
from app.domain.entities.location import Location
from app.domain.entities.report import Report
from app.domain.entities.vote import Vote
from app.domain.exceptions.report import ReportNotFoundException


class TestGetReportByIdUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_vote_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_vote_repo):
        return GetReportByIdUseCase(
            report_repo=mock_report_repo, vote_repo=mock_vote_repo
        )

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=uuid.uuid4(),
            title="Single Report",
            issue_type=IssueType.SNOW,
            location=Location(0.0, 0.0),
            user_location=Location(0.0, 0.0),
            created_by_id=uuid.uuid4(),
        )

    async def test_get_report_success_anonymous(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        result = await use_case.execute(sample_report.id)

        assert result.id == sample_report.id
        assert result.current_user_vote is None
        mock_report_repo.get_by_id.assert_called_once_with(sample_report.id)

    async def test_get_report_success_with_user_vote(
        self, use_case, mock_report_repo, mock_vote_repo, sample_report
    ):
        user_id = uuid.uuid4()
        mock_report_repo.get_by_id.return_value = sample_report
        mock_vote_repo.get_user_vote.return_value = Vote(
            user_id=user_id,
            report_id=sample_report.id,
            is_confirm=True,
            user_location=Location(0, 0),
        )

        result = await use_case.execute(
            sample_report.id, current_user_id=user_id
        )

        assert result.id == sample_report.id
        assert result.current_user_vote == VoteType.CONFIRM
        mock_vote_repo.get_user_vote.assert_called_once_with(
            user_id=user_id, report_id=sample_report.id
        )

    async def test_get_report_not_found(self, use_case, mock_report_repo):
        mock_report_repo.get_by_id.return_value = None
        report_id = uuid.uuid4()

        with pytest.raises(ReportNotFoundException):
            await use_case.execute(report_id)

    async def test_get_report_no_vote(
        self, use_case, mock_report_repo, mock_vote_repo, sample_report
    ):
        user_id = uuid.uuid4()
        mock_report_repo.get_by_id.return_value = sample_report
        mock_vote_repo.get_user_vote.return_value = None

        result = await use_case.execute(
            sample_report.id, current_user_id=user_id
        )

        assert result.current_user_vote is None
