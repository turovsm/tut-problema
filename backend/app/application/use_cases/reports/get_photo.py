from uuid import UUID

from app.domain.entities.report import ReportPhoto
from app.domain.exceptions.base import EntityNotFoundException
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class GetPhotoUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    async def execute(self, photo_id: UUID) -> ReportPhoto:
        # 1. Поиск записи о фото в базе данных
        photo = await self.report_repo.get_photo_by_id(photo_id)

        # 2. Если запись не найдена — выбрасываем исключение
        if not photo:
            raise EntityNotFoundException("Photo not found")

        # 3. Возвращаем сущность.
        return photo
