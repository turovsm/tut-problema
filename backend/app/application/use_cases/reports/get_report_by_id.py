from uuid import UUID

from app.domain.entities.enums import VoteType
from app.domain.entities.report import Report
from app.domain.exceptions.report import ReportNotFoundException
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)
from app.domain.interfaces.repositories.vote_repository import IVoteRepository


class GetReportByIdUseCase:
    def __init__(
        self, report_repo: IReportRepository, vote_repo: IVoteRepository
    ):
        self.report_repo = report_repo
        self.vote_repo = vote_repo

    async def execute(
        self, report_id: UUID, current_user_id: UUID | None = None
    ) -> Report:
        # 1. Поиск отчета в репозитории со всеми связями (фото, автор)
        report = await self.report_repo.get_by_id(report_id)

        if not report:
            raise ReportNotFoundException()

        # 2. Если пользователь авторизован, проверяем его голос для этого отчета
        if current_user_id:
            vote = await self.vote_repo.get_user_vote(
                user_id=current_user_id, report_id=report_id
            )

            if vote:
                report.current_user_vote = (
                    VoteType.CONFIRM if vote.is_confirm else VoteType.DISMISS
                )
            else:
                report.current_user_vote = None
        else:
            report.current_user_vote = None

        return report
