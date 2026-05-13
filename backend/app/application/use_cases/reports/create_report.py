from app.application.dto.reports import CreateReportDTO
from app.core.utils.distance import calculate_distance_haversine
from app.domain.entities.location import Location
from app.domain.entities.report import Report, ReportPhoto
from app.domain.exceptions.report import DistanceTooFarException
from app.domain.interfaces.providers.storage_provider import IStorageProvider
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class CreateReportUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        storage_provider: IStorageProvider,
        max_report_distance_meters: int,
        earth_radius: float,
    ):
        self.report_repo = report_repo
        self.storage_provider = storage_provider
        self.max_distance = max_report_distance_meters
        self.earth_radius = earth_radius

    async def execute(self, dto: CreateReportDTO) -> Report:
        # 1. Проверка бизнес-правила: расстояние от пользователя до места проблемы
        distance = calculate_distance_haversine(
            dto.user_location_lat,
            dto.user_location_lng,
            dto.location_lat,
            dto.location_lng,
            earth_radius=self.earth_radius,
        )

        if distance > self.max_distance:
            raise DistanceTooFarException(
                distance=distance, max_allowed=self.max_distance
            )

        # 2. Создание координат
        issue_location = Location(
            longitude=dto.location_lng, latitude=dto.location_lat
        )
        user_loc_snapshot = Location(
            longitude=dto.user_location_lng, latitude=dto.user_location_lat
        )

        # 3. Создание основной сущности отчета
        report = Report(
            title=dto.title,
            description=dto.description,
            issue_type=dto.issue_type,
            location=issue_location,
            user_location=user_loc_snapshot,
            created_by_id=dto.creator_id,
        )

        # 4. Сохранение
        report = await self.report_repo.save(report)

        # 5. Обработка и сохранение фотографий
        for file in dto.files:
            # Сохраняем физический файл через провайдер
            file_path = await self.storage_provider.save_file(
                file=file, subfolder=str(report.id)
            )

            # Создаем сущность фото
            photo = ReportPhoto(
                report_id=report.id,
                file_name=getattr(file, "filename", "unnamed"),
                file_path=file_path,
            )

            # Регистрируем фото в репозитории
            await self.report_repo.add_photo(photo)
            report.photos.append(photo)

        return report
