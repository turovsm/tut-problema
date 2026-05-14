import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.reports import UpdateReportDTO
from app.application.use_cases.reports.update_report import UpdateReportUseCase
from app.domain.entities.enums import ReportStatus, UserRole
from app.domain.entities.location import Location
from app.domain.entities.report import Report
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.exceptions.report import ReportNotFoundException


class TestUpdateReportUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        repo = AsyncMock()
        repo.save.side_effect = lambda x: x
        return repo

    @pytest.fixture
    def use_case(self, mock_report_repo):
        return UpdateReportUseCase(report_repo=mock_report_repo)

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=uuid.uuid4(),
            title="Original Title",
            description="Original Desc",
            issue_type="pothole",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=uuid.uuid4(),
            status=ReportStatus.PENDING,
            assigned_to_id=None,
        )

    async def test_update_success_by_owner(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = UpdateReportDTO(
            report_id=sample_report.id,
            user_id=sample_report.created_by_id,
            user_role=UserRole.USER,
            title="Updated Title",
            description="Updated Desc",
        )

        result = await use_case.execute(dto)

        assert result.title == "Updated Title"
        assert result.description == "Updated Desc"
        mock_report_repo.save.assert_called_once()

    async def test_update_status_by_moderator(
        self, use_case, mock_report_repo, sample_report
    ):
        """Модератор может изменять статус отчета."""
        mock_report_repo.get_by_id.return_value = sample_report

        dto = UpdateReportDTO(
            report_id=sample_report.id,
            user_id=uuid.uuid4(),
            user_role=UserRole.MODERATOR,
            status=ReportStatus.CONFIRMED,
        )

        result = await use_case.execute(dto)

        assert result.status == ReportStatus.CONFIRMED
        mock_report_repo.save.assert_called_once()

    async def test_update_forbidden_for_other_user(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = UpdateReportDTO(
            report_id=sample_report.id,
            user_id=uuid.uuid4(),
            user_role=UserRole.USER,
            title="Hacker title",
        )

        with pytest.raises(PermissionDeniedException):
            await use_case.execute(dto)

        mock_report_repo.save.assert_not_called()

    async def test_update_status_forbidden_for_owner(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = UpdateReportDTO(
            report_id=sample_report.id,
            user_id=sample_report.created_by_id,
            user_role=UserRole.USER,
            status=ReportStatus.RESOLVED,
        )

        with pytest.raises(PermissionDeniedException):
            await use_case.execute(dto)

    async def test_assign_report_success_as_moderator(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report
        assignee_id = uuid.uuid4()

        dto = UpdateReportDTO(
            report_id=sample_report.id,
            user_id=uuid.uuid4(),
            user_role=UserRole.MODERATOR,
            assigned_to_id=assignee_id,
        )

        result = await use_case.execute(dto)

        assert result.assigned_to_id == assignee_id
        mock_report_repo.save.assert_called_once()

    async def test_assign_report_forbidden_for_owner(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = UpdateReportDTO(
            report_id=sample_report.id,
            user_id=sample_report.created_by_id,
            user_role=UserRole.USER,
            assigned_to_id=uuid.uuid4(),
        )

        with pytest.raises(PermissionDeniedException) as exc:
            await use_case.execute(dto)

        assert "permissions to assign reports" in exc.value.message

    async def test_update_report_not_found(self, use_case, mock_report_repo):
        mock_report_repo.get_by_id.return_value = None

        dto = UpdateReportDTO(
            report_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            user_role=UserRole.USER,
        )

        with pytest.raises(ReportNotFoundException):
            await use_case.execute(dto)
