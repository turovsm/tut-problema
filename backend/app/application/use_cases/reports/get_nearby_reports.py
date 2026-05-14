from app.application.dto.reports import NearbyReportsDTO
from app.domain.entities.enums import VoteType
from app.domain.entities.report import Report
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)
from app.domain.interfaces.repositories.vote_repository import IVoteRepository


class GetNearbyReportsUseCase:
    def __init__(
        self, report_repo: IReportRepository, vote_repo: IVoteRepository
    ):
        self.report_repo = report_repo
        self.vote_repo = vote_repo

    async def execute(self, dto: NearbyReportsDTO) -> list[Report]:
        # 1. Получаем список отчетов в заданном радиусе через репозиторий
        reports = await self.report_repo.get_nearby(
            lat=dto.lat, lon=dto.lon, radius_meters=dto.radius, limit=dto.limit
        )

        # 2. Если пользователь авторизован, обогащаем данные его голосами
        if dto.current_user_id and reports:
            report_ids = [r.id for r in reports]
            votes_map = await self.vote_repo.get_votes_for_reports(
                user_id=dto.current_user_id, report_ids=report_ids
            )

            for report in reports:
                user_vote = votes_map.get(report.id)
                if user_vote:
                    report.current_user_vote = (
                        VoteType.CONFIRM
                        if user_vote.is_confirm
                        else VoteType.DISMISS
                    )
                else:
                    report.current_user_vote = None
        else:
            # Сбрасываем поле для неавторизованных пользователей
            for report in reports:
                report.current_user_vote = None

        return reports
