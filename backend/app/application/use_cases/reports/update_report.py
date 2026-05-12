from datetime import datetime, timezone

from app.application.dto.reports import UpdateReportDTO
from app.domain.entities.enums import UserRole
from app.domain.entities.report import Report
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.exceptions.report import ReportNotFoundException
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)
from app.utils.datetime import get_utc_now_naive


class UpdateReportUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    async def execute(self, dto: UpdateReportDTO) -> Report:
        # 1. Поиск отчета в репозитории
        report = await self.report_repo.get_by_id(dto.report_id)
        if not report:
            raise ReportNotFoundException()

        # 2. Проверка прав доступа
        is_owner = report.created_by_id == dto.user_id
        is_staff = dto.user_role in [UserRole.MODERATOR, UserRole.GOV_ORG]

        if not (is_owner or is_staff):
            raise PermissionDeniedException(
                "Not enough permissions to update this report"
            )

        # 3. Применение изменений
        if dto.title is not None:
            report.title = dto.title

        if dto.description is not None:
            report.description = dto.description

        if dto.status is not None:
            if not is_staff:
                raise PermissionDeniedException(
                    "Not enough permissions to update this report"
                )
            report.status = dto.status

        if dto.assigned_to_id is not None:
            if not is_staff:
                raise PermissionDeniedException(
                    "Not enough permissions to assign reports"
                )
            report.assigned_to_id = dto.assigned_to_id

        # Обновляем метку времени изменения
        report.updated_at = get_utc_now_naive()

        # 4. Сохранение обновленной сущности
        return await self.report_repo.save(report)
