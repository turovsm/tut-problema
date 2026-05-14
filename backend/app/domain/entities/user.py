from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.core.utils.datetime import get_utc_now_naive

from .enums import UserRole


@dataclass
class User:
    email: str
    username: str
    password_hash: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=get_utc_now_naive)
