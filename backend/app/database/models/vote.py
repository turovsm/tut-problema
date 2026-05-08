import uuid
from datetime import datetime

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Vote(Base):
    __tablename__ = "votes"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_id: UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_confirm: bool = Column(Boolean, nullable=False)
    user_location: WKBElement = Column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    is_verified: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="votes")
    report = relationship(
        "Report", foreign_keys=[report_id], back_populates="votes"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "report_id", name="unique_user_report_vote"
        ),
        Index("idx_votes_report_id", "report_id"),
        Index("idx_votes_user_id", "user_id"),
        Index("idx_votes_is_confirm", "is_confirm"),
        Index("idx_votes_created_at", "created_at"),
    )
