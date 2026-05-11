from app.application.dto.reports import ReportFilterDTO
from app.domain.entities.enums import VoteType
from app.domain.entities.report import Report
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)
from app.domain.interfaces.repositories.vote_repository import IVoteRepository


class GetReportsUseCase:
    def __init__(
        self, report_repo: IReportRepository, vote_repo: IVoteRepository
    ):
        self.report_repo = report_repo
        self.vote_repo = vote_repo

    async def execute(self, dto: ReportFilterDTO) -> tuple[list[Report], int]:
        # 1. Рассчитываем смещение для пагинации
        offset = (dto.page - 1) * dto.limit

        # 2. Получаем список отчетов и общее количество из репозитория
        reports, total = await self.report_repo.get_list(
            issue_type=dto.issue_type,
            status=dto.status_filter,
            limit=dto.limit,
            offset=offset,
        )

        # 3. Если передан ID пользователя, обогащаем отчеты информацией о голосе
        if dto.current_user_id and reports:
            report_ids = [r.id for r in reports]
            votes_map = await self.vote_repo.get_votes_for_reports(
                user_id=dto.current_user_id, report_ids=report_ids
            )

            for report in reports:
                user_vote = votes_map.get(report.id)
                if user_vote:
                    # Устанавливаем строковое значение
                    report.current_user_vote = (
                        VoteType.CONFIRM
                        if user_vote.is_confirm
                        else VoteType.DISMISS
                    )
                else:
                    report.current_user_vote = None
        else:
            # Если пользователь не авторизован, голоса всегда None
            for report in reports:
                report.current_user_vote = None

        return reports, total
