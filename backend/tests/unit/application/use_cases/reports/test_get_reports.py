import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.reports import ReportFilterDTO
from app.application.use_cases.reports.get_reports import GetReportsUseCase
from app.domain.entities.enums import IssueType, ReportStatus, VoteType
from app.domain.entities.location import Location
from app.domain.entities.report import Report
from app.domain.entities.vote import Vote


class TestGetReportsUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_vote_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_vote_repo):
        return GetReportsUseCase(
            report_repo=mock_report_repo, vote_repo=mock_vote_repo
        )

    @pytest.fixture
    def sample_reports(self):
        rep1 = Report(
            id=uuid.uuid4(),
            title="Issue 1",
            issue_type=IssueType.SNOW,
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=uuid.uuid4(),
            status=ReportStatus.PENDING,
        )
        rep2 = Report(
            id=uuid.uuid4(),
            title="Issue 2",
            issue_type=IssueType.POTHOLE,
            location=Location(1, 1),
            user_location=Location(1, 1),
            created_by_id=uuid.uuid4(),
            status=ReportStatus.PENDING,
        )
        return [rep1, rep2]

    async def test_get_reports_anonymous(
        self, use_case, mock_report_repo, sample_reports
    ):
        mock_report_repo.get_list.return_value = (
            sample_reports,
            10,
        )

        dto = ReportFilterDTO(page=1, limit=5, current_user_id=None)

        reports, total = await use_case.execute(dto)

        assert total == 10
        assert len(reports) == 2
        assert reports[0].current_user_vote is None
        mock_report_repo.get_list.assert_called_once_with(
            issue_type=None, status=None, limit=5, offset=0
        )

    async def test_get_reports_with_user_enrichment(
        self, use_case, mock_report_repo, mock_vote_repo, sample_reports
    ):
        user_id = uuid.uuid4()
        rep1, rep2 = sample_reports

        mock_report_repo.get_list.return_value = (sample_reports, 2)

        mock_vote_repo.get_votes_for_reports.return_value = {
            rep1.id: Vote(
                user_id=user_id,
                report_id=rep1.id,
                is_confirm=True,
                user_location=Location(0, 0),
            )
        }

        dto = ReportFilterDTO(page=2, limit=10, current_user_id=user_id)

        reports, _ = await use_case.execute(dto)

        assert reports[0].id == rep1.id
        assert reports[0].current_user_vote == VoteType.CONFIRM

        assert reports[1].id == rep2.id
        assert reports[1].current_user_vote is None

        mock_report_repo.get_list.assert_called_once_with(
            issue_type=None, status=None, limit=10, offset=10
        )
        mock_vote_repo.get_votes_for_reports.assert_called_once_with(
            user_id=user_id, report_ids=[rep1.id, rep2.id]
        )

    async def test_get_reports_filtering(self, use_case, mock_report_repo):
        mock_report_repo.get_list.return_value = ([], 0)

        dto = ReportFilterDTO(
            issue_type=IssueType.FLOODING, status_filter=ReportStatus.CONFIRMED
        )

        await use_case.execute(dto)

        mock_report_repo.get_list.assert_called_once_with(
            issue_type=IssueType.FLOODING,
            status=ReportStatus.CONFIRMED,
            limit=20,
            offset=0,
        )
