import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.reports.delete_report import DeleteReportUseCase
from app.domain.entities.enums import UserRole
from app.domain.entities.location import Location
from app.domain.entities.report import Report, ReportPhoto
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.exceptions.report import ReportNotFoundException


class TestDeleteReportUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_storage_provider(self):
        return AsyncMock()

    @pytest.fixture
    def mock_logger(self, mocker):
        return mocker.patch(
            "app.application.use_cases.reports.delete_report.logger"
        )

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_storage_provider):
        return DeleteReportUseCase(
            report_repo=mock_report_repo,
            storage_provider=mock_storage_provider,
        )

    @pytest.fixture
    def sample_report(self):
        report_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        photos = [
            ReportPhoto(
                report_id=report_id, file_name="1.jpg", file_path="path/1.jpg"
            ),
            ReportPhoto(
                report_id=report_id, file_name="2.jpg", file_path="path/2.jpg"
            ),
        ]
        return Report(
            id=report_id,
            title="Title",
            issue_type="pothole",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=owner_id,
            photos=photos,
        )

    async def test_delete_success_by_owner(
        self, use_case, mock_report_repo, mock_storage_provider, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        await use_case.execute(
            report_id=sample_report.id,
            user_id=sample_report.created_by_id,
            user_role=UserRole.USER,
        )

        mock_report_repo.delete.assert_called_once_with(sample_report.id)

        assert mock_storage_provider.delete_file.call_count == 2
        mock_storage_provider.delete_file.assert_any_call("path/1.jpg")
        mock_storage_provider.delete_file.assert_any_call("path/2.jpg")

    async def test_delete_success_by_moderator(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        await use_case.execute(
            report_id=sample_report.id,
            user_id=uuid.uuid4(),
            user_role=UserRole.MODERATOR,
        )

        mock_report_repo.delete.assert_called_once()

    async def test_delete_forbidden(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        with pytest.raises(PermissionDeniedException):
            await use_case.execute(
                report_id=sample_report.id,
                user_id=uuid.uuid4(),
                user_role=UserRole.USER,
            )

        mock_report_repo.delete.assert_not_called()

    async def test_delete_report_not_found(self, use_case, mock_report_repo):
        mock_report_repo.get_by_id.return_value = None

        with pytest.raises(ReportNotFoundException):
            await use_case.execute(uuid.uuid4(), uuid.uuid4(), UserRole.USER)

    async def test_delete_continues_on_storage_error(
        self,
        use_case,
        mock_report_repo,
        mock_storage_provider,
        sample_report,
        mock_logger,
    ):
        mock_report_repo.get_by_id.return_value = sample_report
        mock_storage_provider.delete_file.side_effect = [
            Exception("Disk error"),
            None,
        ]

        await use_case.execute(
            report_id=sample_report.id,
            user_id=sample_report.created_by_id,
            user_role=UserRole.USER,
        )

        mock_logger.warning.assert_called_once()

        args, kwargs = mock_logger.warning.call_args
        assert "Could not delete physical file" in args[0]
        assert kwargs["report_id"] == str(sample_report.id)
        assert kwargs["error"] == "Disk error"

        assert mock_storage_provider.delete_file.call_count == 2
        mock_report_repo.delete.assert_called_once()
