import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.reports.delete_report_photo import (
    DeleteReportPhotoUseCase,
)
from app.domain.entities.enums import UserRole
from app.domain.entities.location import Location
from app.domain.entities.report import Report, ReportPhoto
from app.domain.exceptions.base import (
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.domain.exceptions.report import (
    MinPhotosRequiredException,
)


class TestDeleteReportPhotoUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_storage_provider(self):
        return AsyncMock()

    @pytest.fixture
    def mock_logger(self, mocker):
        return mocker.patch(
            "app.application.use_cases.reports.delete_report_photo.logger"
        )

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_storage_provider):
        return DeleteReportPhotoUseCase(
            report_repo=mock_report_repo,
            storage_provider=mock_storage_provider,
            min_photos_per_report=1,
        )

    @pytest.fixture
    def sample_data(self):
        report_id = uuid.uuid4()
        owner_id = uuid.uuid4()

        photo1 = ReportPhoto(
            id=uuid.uuid4(),
            report_id=report_id,
            file_name="1.jpg",
            file_path="p1.jpg",
        )
        photo2 = ReportPhoto(
            id=uuid.uuid4(),
            report_id=report_id,
            file_name="2.jpg",
            file_path="p2.jpg",
        )

        report = Report(
            id=report_id,
            title="Test",
            issue_type="other",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=owner_id,
            photos=[photo1, photo2],
        )
        return report, photo1, photo2

    async def test_delete_photo_success_by_owner(
        self, use_case, mock_report_repo, mock_storage_provider, sample_data
    ):
        report, photo1, _ = sample_data
        mock_report_repo.get_photo_by_id.return_value = photo1
        mock_report_repo.get_by_id.return_value = report

        await use_case.execute(
            photo_id=photo1.id,
            user_id=report.created_by_id,
            user_role=UserRole.USER,
        )

        mock_report_repo.delete_photo.assert_called_once_with(photo1.id)
        mock_storage_provider.delete_file.assert_called_once_with(
            photo1.file_path
        )

    async def test_delete_photo_success_by_moderator(
        self, use_case, mock_report_repo, mock_storage_provider, sample_data
    ):
        report, photo1, _ = sample_data
        mock_report_repo.get_photo_by_id.return_value = photo1
        mock_report_repo.get_by_id.return_value = report

        await use_case.execute(
            photo_id=photo1.id,
            user_id=uuid.uuid4(),
            user_role=UserRole.MODERATOR,
        )

        mock_report_repo.delete_photo.assert_called_once_with(photo1.id)
        mock_storage_provider.delete_file.assert_called_once_with(
            photo1.file_path
        )

    async def test_delete_photo_min_limit_violation(
        self, use_case, mock_report_repo, sample_data
    ):
        report, photo1, _ = sample_data
        report.photos = [photo1]
        mock_report_repo.get_photo_by_id.return_value = photo1
        mock_report_repo.get_by_id.return_value = report

        with pytest.raises(MinPhotosRequiredException):
            await use_case.execute(
                photo_id=photo1.id,
                user_id=report.created_by_id,
                user_role=UserRole.USER,
            )

        mock_report_repo.delete_photo.assert_not_called()

    async def test_delete_photo_forbidden(
        self, use_case, mock_report_repo, sample_data
    ):
        report, photo1, _ = sample_data
        mock_report_repo.get_photo_by_id.return_value = photo1
        mock_report_repo.get_by_id.return_value = report

        with pytest.raises(PermissionDeniedException):
            await use_case.execute(
                photo_id=photo1.id,
                user_id=uuid.uuid4(),
                user_role=UserRole.USER,
            )

    async def test_delete_photo_not_found(self, use_case, mock_report_repo):
        mock_report_repo.get_photo_by_id.return_value = None

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(uuid.uuid4(), uuid.uuid4(), UserRole.USER)

    async def test_delete_photo_storage_error_logged(
        self,
        use_case,
        mock_report_repo,
        mock_storage_provider,
        sample_data,
        mock_logger,
    ):
        report, photo1, _ = sample_data
        mock_report_repo.get_photo_by_id.return_value = photo1
        mock_report_repo.get_by_id.return_value = report
        mock_storage_provider.delete_file.side_effect = Exception("Disk full")

        await use_case.execute(
            photo_id=photo1.id,
            user_id=report.created_by_id,
            user_role=UserRole.USER,
        )

        mock_report_repo.delete_photo.assert_called_once()
        mock_logger.warning.assert_called_once()
