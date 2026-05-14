from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.core.utils.datetime import get_utc_now_naive


@dataclass
class RefreshToken:
    jti: str
    user_id: UUID
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass
class VerificationToken:
    user_id: UUID
    token: UUID = field(default_factory=uuid4)
    expires_at: datetime = field(default_factory=get_utc_now_naive)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=get_utc_now_naive)
