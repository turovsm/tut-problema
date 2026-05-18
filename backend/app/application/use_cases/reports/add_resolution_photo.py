from typing import Any
from uuid import UUID

from app.domain.entities.report import ResolutionPhoto
from app.domain.exceptions.base import EntityNotFoundException
from app.domain.exceptions.report import PhotoLimitExceededException
from app.domain.interfaces.providers.storage_provider import IStorageProvider
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class AddResolutionPhotoUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        storage_provider: IStorageProvider,
        max_photos: int,
    ):
        self.report_repo = report_repo
        self.storage_provider = storage_provider
        self.max_photos = max_photos

    async def execute(self, resolution_id: UUID, file: Any) -> ResolutionPhoto:
        # 1. Поиск решения
        resolution = await self.report_repo.get_resolution_by_id(resolution_id)
        if not resolution:
            raise EntityNotFoundException("Resolution not found")

        # 2. Проверка лимита
        if len(resolution.photos) >= self.max_photos:
            raise PhotoLimitExceededException(max_photos=self.max_photos)

        # 3. Сохранение файла в хранилище
        file_path = await self.storage_provider.save_file(
            file=file, subfolder=f"resolutions/{resolution.id}"
        )

        # 4. Создание сущности фото и сохранение в БД
        photo = ResolutionPhoto(
            resolution_id=resolution.id,
            file_name=getattr(file, "filename", "unnamed"),
            file_path=file_path,
        )

        return await self.report_repo.add_resolution_photo(photo)
