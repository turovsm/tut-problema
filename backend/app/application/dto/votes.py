from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.enums import ReportStatus, VoteType


@dataclass(frozen=True)
class CastVoteDTO:
    user_id: UUID
    report_id: UUID
    vote_type: VoteType
    user_location_lng: float
    user_location_lat: float
    accuracy: float | None = None


@dataclass(frozen=True)
class VoteStatsDTO:
    report_id: UUID
    confirm_count: int
    dismiss_count: int
    current_status: ReportStatus


@dataclass(frozen=True)
class UserVotesFilterDTO:
    user_id: UUID
    page: int = 1
    limit: int = 20
