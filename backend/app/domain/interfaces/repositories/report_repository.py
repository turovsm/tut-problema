from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.enums import IssueType, ReportStatus
from app.domain.entities.report import (
    Report,
    ReportPhoto,
    ReportResolution,
    ResolutionPhoto,
)


class IReportRepository(ABC):
    @abstractmethod
    async def get_by_id(self, report_id: UUID) -> Report | None: ...

    @abstractmethod
    async def save(self, report: Report) -> Report: ...

    @abstractmethod
    async def delete(self, report_id: UUID) -> None: ...

    @abstractmethod
    async def get_list(
        self,
        issue_type: IssueType | None = None,
        status: ReportStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Report], int]: ...

    @abstractmethod
    async def get_nearby(
        self, lat: float, lon: float, radius_meters: int, limit: int
    ) -> list[Report]: ...

    @abstractmethod
    async def get_by_user(
        self, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[Report], int]: ...

    @abstractmethod
    async def add_photo(self, photo: ReportPhoto) -> ReportPhoto: ...

    @abstractmethod
    async def get_photo_by_id(self, photo_id: UUID) -> ReportPhoto | None: ...

    @abstractmethod
    async def delete_photo(self, photo_id: UUID) -> None: ...

    @abstractmethod
    async def save_resolution(
        self, resolution: ReportResolution
    ) -> ReportResolution: ...

    @abstractmethod
    async def add_resolution_photo(
        self, photo: ResolutionPhoto
    ) -> ResolutionPhoto: ...

    @abstractmethod
    async def get_resolution_photo_by_id(
        self, photo_id: UUID
    ) -> ResolutionPhoto | None: ...

    @abstractmethod
    async def get_resolution_by_id(
        self, resolution_id: UUID
    ) -> ReportResolution | None: ...

    @abstractmethod
    async def delete_resolution_photo(self, photo_id: UUID) -> None: ...
