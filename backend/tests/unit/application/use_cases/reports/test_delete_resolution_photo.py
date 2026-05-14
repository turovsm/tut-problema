import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.reports.delete_resolution_photo import (
    DeleteResolutionPhotoUseCase,
)
from app.domain.entities.report import ResolutionPhoto
from app.domain.exceptions.base import EntityNotFoundException


class TestDeleteResolutionPhotoUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_storage_provider(self):
        return AsyncMock()

    @pytest.fixture
    def mock_logger(self, mocker):
        return mocker.patch(
            "app.application.use_cases.reports.delete_resolution_photo.logger"
        )

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_storage_provider):
        return DeleteResolutionPhotoUseCase(
            report_repo=mock_report_repo,
            storage_provider=mock_storage_provider,
        )

    async def test_delete_resolution_photo_success(
        self, use_case, mock_report_repo, mock_storage_provider
    ):
        photo_id = uuid.uuid4()
        photo_entity = ResolutionPhoto(
            id=photo_id,
            resolution_id=uuid.uuid4(),
            file_name="res.jpg",
            file_path="uploads/resolutions/123/res.jpg",
        )
        mock_report_repo.get_resolution_photo_by_id.return_value = photo_entity

        await use_case.execute(photo_id)

        mock_report_repo.delete_resolution_photo.assert_called_once_with(
            photo_id
        )

        mock_storage_provider.delete_file.assert_called_once_with(
            "uploads/resolutions/123/res.jpg"
        )

    async def test_delete_resolution_photo_not_found(
        self, use_case, mock_report_repo
    ):
        mock_report_repo.get_resolution_photo_by_id.return_value = None
        photo_id = uuid.uuid4()

        with pytest.raises(EntityNotFoundException) as exc:
            await use_case.execute(photo_id)

        assert "Resolution photo not found" in exc.value.message
        mock_report_repo.delete_resolution_photo.assert_not_called()

    async def test_delete_resolution_photo_storage_error_swallowed(
        self, use_case, mock_report_repo, mock_storage_provider, mock_logger
    ):
        photo_id = uuid.uuid4()
        photo_entity = ResolutionPhoto(
            id=photo_id,
            resolution_id=uuid.uuid4(),
            file_name="error.jpg",
            file_path="path/to/error.jpg",
        )
        mock_report_repo.get_resolution_photo_by_id.return_value = photo_entity

        mock_storage_provider.delete_file.side_effect = Exception("IO Error")

        await use_case.execute(photo_id)

        mock_report_repo.delete_resolution_photo.assert_called_once_with(
            photo_id
        )

        mock_logger.warning.assert_called_once()
        args, kwargs = mock_logger.warning.call_args
        assert "Failed to delete physical photo file" in args[0]
        assert kwargs["photo_id"] == str(photo_id)
