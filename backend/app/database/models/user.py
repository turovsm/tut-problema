import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: str = Column(String(255), unique=True, nullable=False)
    username: str = Column(String(50), unique=True, nullable=False)
    password_hash: str = Column(String(255), nullable=False)
    role: str = Column(
        Enum("user", "moderator", "gov_org", name="user_roles"), default="user"
    )
    is_active: bool = Column(Boolean, default=True)
    is_verified: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, server_default=func.now())

    reports = relationship(
        "Report",
        foreign_keys="Report.created_by_id",
        back_populates="created_by",
    )
    votes = relationship(
        "Vote", foreign_keys="Vote.user_id", back_populates="user"
    )
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    verification_tokens = relationship(
        "VerificationToken", back_populates="user", cascade="all, delete-orphan"
    )
