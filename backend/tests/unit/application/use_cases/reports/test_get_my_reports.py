import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.reports.get_my_reports import (
    GetMyReportsUseCase,
)
from app.domain.entities.enums import IssueType, VoteType
from app.domain.entities.location import Location
from app.domain.entities.report import Report


class TestGetMyReportsUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_report_repo):
        return GetMyReportsUseCase(report_repo=mock_report_repo)

    @pytest.fixture
    def sample_reports(self):
        user_id = uuid.uuid4()
        return (
            [
                Report(
                    id=uuid.uuid4(),
                    title="My Issue 1",
                    issue_type=IssueType.SNOW,
                    location=Location(0, 0),
                    user_location=Location(0, 0),
                    created_by_id=user_id,
                ),
                Report(
                    id=uuid.uuid4(),
                    title="My Issue 2",
                    issue_type=IssueType.POTHOLE,
                    location=Location(1, 1),
                    user_location=Location(1, 1),
                    created_by_id=user_id,
                    current_user_vote=VoteType.CONFIRM,
                ),
            ],
            2,
        )

    async def test_get_my_reports_success(
        self, use_case, mock_report_repo, sample_reports
    ):
        reports_list, total_count = sample_reports
        user_id = reports_list[0].created_by_id
        mock_report_repo.get_by_user.return_value = (reports_list, total_count)

        reports, total = await use_case.execute(
            user_id=user_id, page=2, limit=10
        )

        mock_report_repo.get_by_user.assert_called_once_with(
            user_id=user_id, limit=10, offset=10
        )

        assert total == 2
        assert len(reports) == 2
        assert reports[0].title == "My Issue 1"

        assert reports[1].current_user_vote is None

    async def test_get_my_reports_empty(self, use_case, mock_report_repo):
        user_id = uuid.uuid4()
        mock_report_repo.get_by_user.return_value = ([], 0)

        reports, total = await use_case.execute(user_id=user_id)

        assert total == 0
        assert reports == []
