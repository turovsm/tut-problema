import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.reports import ResolveReportDTO
from app.application.use_cases.reports.resolve_report import (
    ResolveReportUseCase,
)
from app.domain.entities.enums import ReportStatus
from app.domain.entities.location import Location
from app.domain.entities.report import Report, ReportResolution
from app.domain.exceptions.base import (
    BusinessRuleException,
    PermissionDeniedException,
)
from app.domain.exceptions.report import (
    PhotoLimitExceededException,
)


class TestResolveReportUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        repo = AsyncMock()
        repo.save.side_effect = lambda x: x
        repo.save_resolution.side_effect = lambda x: x
        return repo

    @pytest.fixture
    def mock_storage_provider(self):
        provider = AsyncMock()
        provider.save_file.return_value = "path/res.jpg"
        return provider

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_storage_provider):
        return ResolveReportUseCase(
            report_repo=mock_report_repo,
            storage_provider=mock_storage_provider,
            max_photos=3,
        )

    @pytest.fixture
    def assigned_report(self):
        assignee_id = uuid.uuid4()
        return Report(
            id=uuid.uuid4(),
            title="Test",
            issue_type="other",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=uuid.uuid4(),
            assigned_to_id=assignee_id,
            status=ReportStatus.PENDING,
        )

    async def test_resolve_success(
        self, use_case, mock_report_repo, assigned_report
    ):
        mock_report_repo.get_by_id.return_value = assigned_report

        dto = ResolveReportDTO(
            report_id=assigned_report.id,
            resolved_by_id=assigned_report.assigned_to_id,
            comment="Everything is fixed",
            files=[MagicMock()],
        )

        result = await use_case.execute(dto)

        assert isinstance(result, ReportResolution)
        assert assigned_report.status == ReportStatus.RESOLVED
        assert result.comment == "Everything is fixed"
        mock_report_repo.save.assert_called_once()
        mock_report_repo.save_resolution.assert_called_once()
        mock_report_repo.add_resolution_photo.assert_called_once()

    async def test_resolve_already_resolved(
        self, use_case, mock_report_repo, assigned_report
    ):
        assigned_report.status = ReportStatus.RESOLVED
        mock_report_repo.get_by_id.return_value = assigned_report

        dto = ResolveReportDTO(
            assigned_report.id, assigned_report.assigned_to_id, "done"
        )

        with pytest.raises(BusinessRuleException) as exc:
            await use_case.execute(dto)
        assert "already resolved" in exc.value.message

    async def test_resolve_unassigned(
        self, use_case, mock_report_repo, assigned_report
    ):
        assigned_report.assigned_to_id = None
        mock_report_repo.get_by_id.return_value = assigned_report

        dto = ResolveReportDTO(assigned_report.id, uuid.uuid4(), "done")

        with pytest.raises(BusinessRuleException) as exc:
            await use_case.execute(dto)
        assert "unassigned report" in exc.value.message

    async def test_resolve_wrong_assignee(
        self, use_case, mock_report_repo, assigned_report
    ):
        mock_report_repo.get_by_id.return_value = assigned_report

        dto = ResolveReportDTO(
            report_id=assigned_report.id,
            resolved_by_id=uuid.uuid4(),
            comment="done",
        )

        with pytest.raises(PermissionDeniedException) as exc:
            await use_case.execute(dto)
        assert "assigned to you" in exc.value.message

    async def test_resolve_photo_limit(
        self, use_case, mock_report_repo, assigned_report
    ):
        mock_report_repo.get_by_id.return_value = assigned_report

        dto = ResolveReportDTO(
            report_id=assigned_report.id,
            resolved_by_id=assigned_report.assigned_to_id,
            comment="done",
            files=[MagicMock()] * 4,
        )

        with pytest.raises(PhotoLimitExceededException):
            await use_case.execute(dto)
