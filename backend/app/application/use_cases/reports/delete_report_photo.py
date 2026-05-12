from uuid import UUID

from app.domain.entities.enums import UserRole
from app.domain.exceptions.base import (
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.domain.exceptions.report import (
    MinPhotosRequiredException,
    ReportNotFoundException,
)
from app.domain.interfaces.providers.storage_provider import IStorageProvider
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class DeleteReportPhotoUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        storage_provider: IStorageProvider,
        min_photos_per_report: int,
    ):
        self.report_repo = report_repo
        self.storage_provider = storage_provider
        self.min_photos = min_photos_per_report

    async def execute(
        self, photo_id: UUID, user_id: UUID, user_role: str
    ) -> None:
        # 1. Поиск информации о фотографии
        photo = await self.report_repo.get_photo_by_id(photo_id)
        if not photo:
            raise EntityNotFoundException("Photo not found")

        # 2. Поиск отчета, к которому относится фото, для проверки прав
        report = await self.report_repo.get_by_id(photo.report_id)
        if not report:
            raise ReportNotFoundException()

        # 3. Проверка прав доступа
        is_owner = report.created_by_id == user_id
        is_staff = user_role in [UserRole.MODERATOR, UserRole.GOV_ORG]

        if not (is_owner or is_staff):
            raise PermissionDeniedException(
                "Not enough permissions to delete this photo"
            )

        # 4. Проверка бизнес-правила: минимальное количество фото
        if len(report.photos) <= self.min_photos:
            raise MinPhotosRequiredException(min_photos=self.min_photos)

        # 5. Удаление записи из репозитория
        await self.report_repo.delete_photo(photo_id)

        # 6. Удаление физического файла через провайдер
        try:
            await self.storage_provider.delete_file(photo.file_path)
        except Exception:
            pass
