from app.application.dto.votes import CastVoteDTO
from app.domain.entities.enums import VoteType
from app.domain.entities.location import Location
from app.domain.entities.vote import Vote
from app.domain.exceptions.report import ReportNotFoundException
from app.domain.exceptions.vote import (
    SelfVotingException,
    VoteDistanceException,
)
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)
from app.domain.interfaces.repositories.vote_repository import IVoteRepository
from app.utils.distance import calculate_distance_haversine


class CastVoteUseCase:
    def __init__(
        self,
        vote_repo: IVoteRepository,
        report_repo: IReportRepository,
        max_vote_distance_meters: int,
        verification_buffer_meters: int,
        earth_radius: float,
    ):
        self.vote_repo = vote_repo
        self.report_repo = report_repo
        self.max_distance = max_vote_distance_meters
        self.buffer = verification_buffer_meters
        self.earth_radius = earth_radius

    async def execute(self, dto: CastVoteDTO) -> Vote:
        # 1. Проверка существования отчета
        report = await self.report_repo.get_by_id(dto.report_id)
        if not report:
            raise ReportNotFoundException()

        # 2. Бизнес-правило: нельзя голосовать за свой собственный отчет
        if report.created_by_id == dto.user_id:
            raise SelfVotingException()

        # 3. Расчет дистанции между пользователем и инцидентом
        distance = calculate_distance_haversine(
            dto.user_location_lat,
            dto.user_location_lng,
            report.location.latitude,
            report.location.longitude,
            earth_radius=self.earth_radius,
        )

        # 4. Проверка: может ли пользователь вообще голосовать
        if distance > self.max_distance:
            raise VoteDistanceException(max_meters=self.max_distance)

        # 5. Определение верификации голоса
        is_verified = False
        if dto.accuracy is not None:
            if distance <= (dto.accuracy + self.buffer):
                is_verified = True

        # 6. Проверка существования предыдущего голоса от этого пользователя
        existing_vote = await self.vote_repo.get_user_vote(
            user_id=dto.user_id, report_id=dto.report_id
        )

        is_confirm = dto.vote_type == VoteType.CONFIRM
        user_loc_snapshot = Location(
            longitude=dto.user_location_lng, latitude=dto.user_location_lat
        )

        if existing_vote:
            # Обновляем существующий голос
            existing_vote.is_confirm = is_confirm
            existing_vote.user_location = user_loc_snapshot
            existing_vote.is_verified = is_verified
            return await self.vote_repo.save(existing_vote)

        # 7. Создание нового голоса
        vote = Vote(
            user_id=dto.user_id,
            report_id=dto.report_id,
            is_confirm=is_confirm,
            user_location=user_loc_snapshot,
            is_verified=is_verified,
        )

        return await self.vote_repo.save(vote)
