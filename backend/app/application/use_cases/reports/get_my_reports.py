from uuid import UUID

from app.domain.entities.report import Report
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class GetMyReportsUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    async def execute(
        self, user_id: UUID, page: int = 1, limit: int = 20
    ) -> tuple[list[Report], int]:
        # 1. Расчет смещения
        offset = (page - 1) * limit

        # 2. Получение данных из репозитория
        reports, total = await self.report_repo.get_by_user(
            user_id=user_id, limit=limit, offset=offset
        )

        for report in reports:
            report.current_user_vote = None

        return reports, total
