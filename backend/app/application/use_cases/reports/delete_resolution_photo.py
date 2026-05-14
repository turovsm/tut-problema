from uuid import UUID

from app.core.logging_config import get_logger
from app.domain.exceptions.base import EntityNotFoundException
from app.domain.interfaces.providers.storage_provider import IStorageProvider
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)

logger = get_logger(__name__)


class DeleteResolutionPhotoUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        storage_provider: IStorageProvider,
    ):
        self.report_repo = report_repo
        self.storage_provider = storage_provider

    async def execute(self, photo_id: UUID) -> None:
        # 1. Ищем фото
        photo = await self.report_repo.get_resolution_photo_by_id(photo_id)
        if not photo:
            raise EntityNotFoundException("Resolution photo not found")

        # 2. Удаление записи из репозитория
        await self.report_repo.delete_resolution_photo(photo_id)

        # 3. Удаление физического файла через провайдер
        try:
            await self.storage_provider.delete_file(photo.file_path)
        except Exception as e:
            logger.warning(
                "Failed to delete physical photo file",
                photo_id=str(photo_id),
                file_path=photo.file_path,
                error=str(e),
            )
