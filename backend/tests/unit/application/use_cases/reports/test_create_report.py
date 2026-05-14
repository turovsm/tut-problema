import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.reports import CreateReportDTO
from app.application.use_cases.reports.create_report import CreateReportUseCase
from app.domain.entities.report import Report
from app.domain.exceptions.report import DistanceTooFarException


class TestCreateReportUseCase:
    @pytest.fixture
    def mock_report_repo(self):
        repo = AsyncMock()
        repo.save.side_effect = lambda x: x
        return repo

    @pytest.fixture
    def mock_storage_provider(self):
        provider = AsyncMock()
        provider.save_file.return_value = "uploads/report_id/photo.jpg"
        return provider

    @pytest.fixture
    def use_case(self, mock_report_repo, mock_storage_provider):
        return CreateReportUseCase(
            report_repo=mock_report_repo,
            storage_provider=mock_storage_provider,
            max_report_distance_meters=1000,
            earth_radius=6371000.0,
        )

    async def test_create_report_success(
        self, use_case, mock_report_repo, mock_storage_provider
    ):
        user_id = uuid.uuid4()
        mock_file = MagicMock()
        mock_file.filename = "pothole.jpg"

        dto = CreateReportDTO(
            title="Deep pothole",
            description="Danger for cars",
            issue_type="pothole",
            location_lng=37.6176,
            location_lat=55.7558,
            user_location_lng=37.6177,
            user_location_lat=55.7559,
            creator_id=user_id,
            files=[mock_file],
        )

        result = await use_case.execute(dto)

        assert isinstance(result, Report)
        assert result.title == "Deep pothole"
        assert len(result.photos) == 1

        mock_report_repo.save.assert_called_once()
        mock_storage_provider.save_file.assert_called_once()
        mock_report_repo.add_photo.assert_called_once()

    async def test_create_report_too_far(self, use_case):
        dto = CreateReportDTO(
            title="Far problem",
            description=None,
            issue_type="snow",
            location_lng=37.6176,
            location_lat=55.7558,
            user_location_lng=38.6176,
            user_location_lat=56.7558,
            creator_id=uuid.uuid4(),
            files=[MagicMock()],
        )

        with pytest.raises(DistanceTooFarException):
            await use_case.execute(dto)

    async def test_create_report_multiple_files(
        self, use_case, mock_storage_provider, mock_report_repo
    ):
        dto = CreateReportDTO(
            title="Big blockage",
            description=None,
            issue_type="blockage",
            location_lng=0.0,
            location_lat=0.0,
            user_location_lng=0.0,
            user_location_lat=0.0,
            creator_id=uuid.uuid4(),
            files=[MagicMock(), MagicMock(), MagicMock()],
        )

        await use_case.execute(dto)

        assert mock_storage_provider.save_file.call_count == 3
        assert mock_report_repo.add_photo.call_count == 3
