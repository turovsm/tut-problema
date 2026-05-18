import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.reports.add_resolution_photo import (
    AddResolutionPhotoUseCase,
)
from app.domain.entities.report import ReportResolution, ResolutionPhoto
from app.domain.exceptions.base import EntityNotFoundException
from app.domain.exceptions.report import PhotoLimitExceededException


class TestAddResolutionPhotoUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        repo = AsyncMock()
        res = ReportResolution(
            id=uuid.uuid4(),
            report_id=uuid.uuid4(),
            resolved_by_id=uuid.uuid4(),
            comment="Fixed",
            photos=[],
        )
        repo.get_resolution_by_id.return_value = res
        repo.add_resolution_photo.side_effect = lambda x: x
        return repo

    @pytest.fixture
    def mock_storage_provider(self):
        provider = AsyncMock()
        provider.save_file.return_value = (
            "uploads/resolutions/res_id/photo.jpg"
        )
        return provider

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_storage_provider):

        return AddResolutionPhotoUseCase(
            report_repo=mock_report_repo,
            storage_provider=mock_storage_provider,
            max_photos=2,
        )

    async def test_add_resolution_photo_success(
        self, use_case, mock_report_repo, mock_storage_provider
    ):
        res_id = uuid.uuid4()
        mock_file = MagicMock()
        mock_file.filename = "fixed_pothole.jpg"

        result = await use_case.execute(resolution_id=res_id, file=mock_file)

        assert isinstance(result, ResolutionPhoto)
        assert result.file_path == "uploads/resolutions/res_id/photo.jpg"

        mock_storage_provider.save_file.assert_called_once()
        _, kwargs = mock_storage_provider.save_file.call_args
        assert "resolutions/" in kwargs["subfolder"]

        mock_report_repo.add_resolution_photo.assert_called_once()

    async def test_add_resolution_photo_not_found(
        self, use_case, mock_report_repo
    ):
        mock_report_repo.get_resolution_by_id.return_value = None

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(
                resolution_id=uuid.uuid4(), file=MagicMock()
            )

    async def test_add_resolution_photo_limit_exceeded(
        self, use_case, mock_report_repo
    ):
        resolution = mock_report_repo.get_resolution_by_id.return_value
        resolution.photos = [MagicMock(), MagicMock()]

        with pytest.raises(PhotoLimitExceededException):
            await use_case.execute(
                resolution_id=resolution.id, file=MagicMock()
            )

        mock_report_repo.add_resolution_photo.assert_not_called()
