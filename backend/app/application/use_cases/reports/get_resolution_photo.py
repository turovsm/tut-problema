from uuid import UUID

from app.domain.entities.report import ResolutionPhoto
from app.domain.exceptions.base import EntityNotFoundException
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class GetResolutionPhotoUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    async def execute(self, photo_id: UUID) -> ResolutionPhoto:
        photo = await self.report_repo.get_resolution_photo_by_id(photo_id)

        if not photo:
            raise EntityNotFoundException("Resolution photo not found")

        return photo
