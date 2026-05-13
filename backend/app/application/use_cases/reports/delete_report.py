from uuid import UUID

from app.core.logging_config import get_logger
from app.domain.entities.enums import UserRole
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.exceptions.report import ReportNotFoundException
from app.domain.interfaces.providers.storage_provider import IStorageProvider
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)

logger = get_logger(__name__)


class DeleteReportUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        storage_provider: IStorageProvider,
    ):
        self.report_repo = report_repo
        self.storage_provider = storage_provider

    async def execute(
        self, report_id: UUID, user_id: UUID, user_role: str
    ) -> None:
        # 1. Поиск отчета и связанных данных
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ReportNotFoundException()

        # 2. Проверка прав доступа
        is_owner = report.created_by_id == user_id
        is_staff = user_role in [UserRole.MODERATOR, UserRole.GOV_ORG]

        if not (is_owner or is_staff):
            raise PermissionDeniedException(
                "Not enough permissions to delete this report"
            )

        # 3. Удаление записи из базы данных
        await self.report_repo.delete(report_id)

        # 4. Удаление физических файлов
        for photo in report.photos:
            try:
                await self.storage_provider.delete_file(photo.file_path)
            except Exception as e:
                logger.warning(
                    "Could not delete physical file during report deletion",
                    report_id=str(report_id),
                    file_path=photo.file_path,
                    error=str(e),
                )
