from app.application.dto.reports import ReportPhotoDTO
from app.domain.entities.enums import UserRole
from app.domain.entities.report import ReportPhoto
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.exceptions.report import (
    PhotoLimitExceededException,
    ReportNotFoundException,
)
from app.domain.interfaces.providers.storage_provider import IStorageProvider
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class AddReportPhotoUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        storage_provider: IStorageProvider,
        max_photos_per_report: int,
    ):
        self.report_repo = report_repo
        self.storage_provider = storage_provider
        self.max_photos = max_photos_per_report

    async def execute(self, dto: ReportPhotoDTO) -> ReportPhoto:
        # 1. Поиск отчета
        report = await self.report_repo.get_by_id(dto.report_id)
        if not report:
            raise ReportNotFoundException()

        # 2. Проверка прав доступа
        is_owner = report.created_by_id == dto.user_id
        is_staff = dto.user_role in [UserRole.MODERATOR, UserRole.GOV_ORG]

        if not (is_owner or is_staff):
            raise PermissionDeniedException(
                "Not enough permissions to add photos to this report"
            )

        # 3. Проверка лимита количества фотографий
        if len(report.photos) >= self.max_photos:
            raise PhotoLimitExceededException(max_photos=self.max_photos)

        # 4. Сохранение файла в хранилище
        file_path = await self.storage_provider.save_file(
            file=dto.file, subfolder=str(report.id)
        )

        # 5. Создание сущности фото и сохранение в БД
        photo = ReportPhoto(
            report_id=report.id,
            file_name=getattr(dto.file, "filename", "unnamed"),
            file_path=file_path,
        )

        await self.report_repo.add_photo(photo)

        return photo
