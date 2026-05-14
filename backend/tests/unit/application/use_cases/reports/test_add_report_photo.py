import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.reports import ReportPhotoDTO
from app.application.use_cases.reports.add_report_photo import (
    AddReportPhotoUseCase,
)
from app.domain.entities.enums import UserRole
from app.domain.entities.location import Location
from app.domain.entities.report import Report, ReportPhoto
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.exceptions.report import (
    PhotoLimitExceededException,
    ReportNotFoundException,
)


class TestAddReportPhotoUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_storage_provider(self):
        provider = AsyncMock()
        provider.save_file.return_value = "path/to/new_photo.jpg"
        return provider

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_storage_provider):
        return AddReportPhotoUseCase(
            report_repo=mock_report_repo,
            storage_provider=mock_storage_provider,
            max_photos_per_report=3,
        )

    @pytest.fixture
    def sample_report(self):
        owner_id = uuid.uuid4()
        return Report(
            id=uuid.uuid4(),
            title="Test",
            issue_type="other",
            location=Location(0, 0),
            user_location=Location(0, 0),
            created_by_id=owner_id,
            photos=[],
        )

    async def test_add_photo_success_by_owner(
        self, use_case, mock_report_repo, mock_storage_provider, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report
        mock_file = MagicMock()
        mock_file.filename = "new.jpg"

        dto = ReportPhotoDTO(
            report_id=sample_report.id,
            user_id=sample_report.created_by_id,
            user_role=UserRole.USER,
            file=mock_file,
        )

        result = await use_case.execute(dto)

        assert isinstance(result, ReportPhoto)
        assert result.file_path == "path/to/new_photo.jpg"
        mock_storage_provider.save_file.assert_called_once()
        mock_report_repo.add_photo.assert_called_once()

    async def test_add_photo_success_by_moderator(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = ReportPhotoDTO(
            report_id=sample_report.id,
            user_id=uuid.uuid4(),
            user_role=UserRole.MODERATOR,
            file=MagicMock(),
        )

        await use_case.execute(dto)
        mock_report_repo.add_photo.assert_called_once()

    async def test_add_photo_forbidden(
        self, use_case, mock_report_repo, sample_report
    ):
        mock_report_repo.get_by_id.return_value = sample_report

        dto = ReportPhotoDTO(
            report_id=sample_report.id,
            user_id=uuid.uuid4(),
            user_role=UserRole.USER,
            file=MagicMock(),
        )

        with pytest.raises(PermissionDeniedException):
            await use_case.execute(dto)

    async def test_add_photo_limit_exceeded(
        self, use_case, mock_report_repo, sample_report
    ):
        sample_report.photos = [MagicMock() for _ in range(3)]
        mock_report_repo.get_by_id.return_value = sample_report

        dto = ReportPhotoDTO(
            report_id=sample_report.id,
            user_id=sample_report.created_by_id,
            user_role=UserRole.USER,
            file=MagicMock(),
        )

        with pytest.raises(PhotoLimitExceededException):
            await use_case.execute(dto)

        mock_report_repo.add_photo.assert_not_called()

    async def test_add_photo_report_not_found(
        self, use_case, mock_report_repo
    ):
        mock_report_repo.get_by_id.return_value = None

        dto = ReportPhotoDTO(
            report_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            user_role=UserRole.USER,
            file=MagicMock(),
        )

        with pytest.raises(ReportNotFoundException):
            await use_case.execute(dto)
