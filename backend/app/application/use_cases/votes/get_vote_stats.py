from uuid import UUID

from app.application.dto.votes import VoteStatsDTO
from app.domain.exceptions.report import ReportNotFoundException
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)
from app.domain.interfaces.repositories.vote_repository import IVoteRepository


class GetVoteStatsUseCase:
    def __init__(
        self, vote_repo: IVoteRepository, report_repo: IReportRepository
    ):
        self.vote_repo = vote_repo
        self.report_repo = report_repo

    async def execute(self, report_id: UUID) -> VoteStatsDTO:
        # 1. Проверяем существование отчета
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ReportNotFoundException()

        # 2. Запрашиваем статистику у репозитория
        stats = await self.vote_repo.get_stats_by_report(report_id)

        # 3. Формируем DTO
        return VoteStatsDTO(
            report_id=report.id,
            confirm_count=stats.get("confirm_count", 0),
            dismiss_count=stats.get("dismiss_count", 0),
            current_status=report.status.value,
        )
