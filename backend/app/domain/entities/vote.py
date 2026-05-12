from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.utils.datetime import get_utc_now_naive

from .location import Location


@dataclass
class Vote:
    user_id: UUID
    report_id: UUID
    is_confirm: bool
    user_location: Location
    is_verified: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=get_utc_now_naive)
