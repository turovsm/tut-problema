from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.utils.datetime import get_utc_now_naive

from .enums import IssueType, ReportStatus, VoteType
from .location import Location
from .user import User


@dataclass
class ReportPhoto:
    file_name: str
    file_path: str
    report_id: UUID
    id: UUID = field(default_factory=uuid4)
    uploaded_at: datetime = field(default_factory=get_utc_now_naive)


@dataclass
class Report:
    title: str
    issue_type: IssueType
    location: Location
    user_location: Location
    created_by_id: UUID
    description: str | None = None
    status: ReportStatus = ReportStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=get_utc_now_naive)
    updated_at: datetime = field(default_factory=get_utc_now_naive)
    photos: list[ReportPhoto] = field(default_factory=list)
    created_by: User | None = None
    current_user_vote: VoteType | None = None
