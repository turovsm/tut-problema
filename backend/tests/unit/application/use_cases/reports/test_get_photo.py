import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.reports.get_photo import GetPhotoUseCase
from app.domain.entities.report import ReportPhoto
from app.domain.exceptions.base import EntityNotFoundException


class TestGetPhotoUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_report_repo):
        return GetPhotoUseCase(report_repo=mock_report_repo)

    async def test_get_photo_success(self, use_case, mock_report_repo):
        photo_id = uuid.uuid4()
        report_id = uuid.uuid4()
        expected_photo = ReportPhoto(
            id=photo_id,
            report_id=report_id,
            file_name="pothole.jpg",
            file_path="uploads/xyz/pothole.jpg",
        )

        mock_report_repo.get_photo_by_id.return_value = expected_photo

        result = await use_case.execute(photo_id)

        assert result == expected_photo
        assert result.file_path == "uploads/xyz/pothole.jpg"
        mock_report_repo.get_photo_by_id.assert_called_once_with(photo_id)

    async def test_get_photo_not_found(self, use_case, mock_report_repo):
        photo_id = uuid.uuid4()
        mock_report_repo.get_photo_by_id.return_value = None

        with pytest.raises(EntityNotFoundException) as exc:
            await use_case.execute(photo_id)

        assert "Photo not found" in exc.value.message
