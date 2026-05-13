from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.domain.entities.enums import IssueType, ReportStatus


@dataclass(frozen=True)
class ReportFilterDTO:
    issue_type: IssueType | None = None
    status_filter: ReportStatus | None = None
    page: int = 1
    limit: int = 20
    current_user_id: UUID | None = None


@dataclass(frozen=True)
class NearbyReportsDTO:
    lat: float
    lon: float
    radius: int
    limit: int
    current_user_id: UUID | None = None


@dataclass(frozen=True)
class CreateReportDTO:
    title: str
    description: str | None
    issue_type: IssueType
    location_lng: float
    location_lat: float
    user_location_lng: float
    user_location_lat: float
    creator_id: UUID
    files: list = field(default_factory=list)


@dataclass(frozen=True)
class UpdateReportDTO:
    report_id: UUID
    user_id: UUID
    user_role: str
    title: str | None = None
    description: str | None = None
    status: ReportStatus | None = None
    assigned_to_id: UUID | None = None


@dataclass(frozen=True)
class ResolveReportDTO:
    report_id: UUID
    resolved_by_id: UUID
    comment: str
    files: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class ReportPhotoDTO:
    report_id: UUID
    user_id: UUID
    user_role: str
    file: Any
