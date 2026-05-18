from app.application.dto.reports import ResolveReportDTO
from app.domain.entities.enums import ReportStatus
from app.domain.entities.report import ReportResolution, ResolutionPhoto
from app.domain.exceptions.base import (
    BusinessRuleException,
    PermissionDeniedException,
)
from app.domain.exceptions.report import (
    PhotoLimitExceededException,
    ReportNotFoundException,
)
from app.domain.interfaces.providers.storage_provider import IStorageProvider
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)


class ResolveReportUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        storage_provider: IStorageProvider,
        max_photos: int,
    ):
        self.report_repo = report_repo
        self.storage_provider = storage_provider
        self.max_photos = max_photos

    async def execute(self, dto: ResolveReportDTO) -> ReportResolution:
        report = await self.report_repo.get_by_id(dto.report_id)
        if not report:
            raise ReportNotFoundException()

        if report.status == ReportStatus.RESOLVED:
            raise BusinessRuleException("Report is already resolved")

        if not report.assigned_to_id:
            raise BusinessRuleException("Cannot resolve an unassigned report")

        if report.assigned_to_id != dto.resolved_by_id:
            raise PermissionDeniedException(
                "You can only resolve reports assigned to you"
            )

        if len(dto.files) > self.max_photos:
            raise PhotoLimitExceededException(max_photos=self.max_photos)

        report.status = ReportStatus.RESOLVED
        await self.report_repo.save(report)

        resolution = ReportResolution(
            report_id=report.id,
            resolved_by_id=dto.resolved_by_id,
            comment=dto.comment,
        )
        resolution = await self.report_repo.save_resolution(resolution)

        for file in dto.files:
            file_path = await self.storage_provider.save_file(
                file=file, subfolder=f"resolutions/{resolution.id}"
            )
            photo = ResolutionPhoto(
                resolution_id=resolution.id,
                file_name=getattr(file, "filename", "unnamed"),
                file_path=file_path,
            )
            await self.report_repo.add_resolution_photo(photo)
            resolution.photos.append(photo)

        return resolution
