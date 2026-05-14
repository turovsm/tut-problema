import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.entities.enums import IssueType, ReportStatus, UserRole


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    reports = relationship(
        "ReportModel",
        back_populates="creator",
        foreign_keys="[ReportModel.created_by_id]",
    )
    votes = relationship("VoteModel", back_populates="user")


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_type: Mapped[IssueType] = mapped_column(
        Enum(IssueType), nullable=False, index=True
    )

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    user_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.PENDING, index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    creator = relationship(
        "UserModel", back_populates="reports", foreign_keys=[created_by_id]
    )
    assignee = relationship("UserModel", foreign_keys=[assigned_to_id])

    photos = relationship(
        "ReportPhotoModel",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    votes = relationship(
        "VoteModel", back_populates="report", cascade="all, delete-orphan"
    )
    resolution = relationship(
        "ReportResolutionModel",
        back_populates="report",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ReportPhotoModel(Base):
    __tablename__ = "report_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    report = relationship("ReportModel", back_populates="photos")


class VoteModel(Base):
    __tablename__ = "votes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    is_confirm: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user = relationship("UserModel", back_populates="votes")
    report = relationship("ReportModel", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("user_id", "report_id", name="uq_user_report_vote"),
        Index("idx_votes_report_confirm", "report_id", "is_confirm"),
    )


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class VerificationTokenModel(Base):
    __tablename__ = "verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ReportResolutionModel(Base):
    __tablename__ = "report_resolutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), unique=True
    )
    resolved_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    report = relationship("ReportModel", back_populates="resolution")
    resolved_by = relationship("UserModel", foreign_keys=[resolved_by_id])
    photos = relationship(
        "ResolutionPhotoModel",
        back_populates="resolution",
        cascade="all, delete-orphan",
    )


class ResolutionPhotoModel(Base):
    __tablename__ = "resolution_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resolution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("report_resolutions.id", ondelete="CASCADE")
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    resolution = relationship("ReportResolutionModel", back_populates="photos")
