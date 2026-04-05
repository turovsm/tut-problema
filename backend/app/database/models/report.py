import uuid
from datetime import datetime

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: str = Column(String(200), nullable=False)
    description: str | None = Column(Text, nullable=True)
    issue_type: str = Column(
        Enum("snow", "pothole", "road_obstruction", "flooding",
             "broken_streetlight", "broken_sidewalk", "water_leak",
             "sewer_overflow", "illegal_dumping", "other",
             name="issue_types"),
        nullable=False
    )
    location: WKBElement = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    user_location: WKBElement = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    status: str = Column(Enum("pending", "confirmed", "dismissed", "resolved", name="report_statuses"),
                         default="pending")
    created_by_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now())
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now())

    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="reports")
    photos = relationship("ReportPhoto", back_populates="report", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_reports_created_by', 'created_by_id'),
        Index('idx_reports_status', 'status'),
        Index('idx_reports_issue_type', 'issue_type'),
        Index('idx_reports_created_at', 'created_at'),
    )


class ReportPhoto(Base):
    __tablename__ = "report_photos"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: UUID = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    file_name: str = Column(String(255), nullable=False)
    file_path: str = Column(String(500), nullable=False)
    uploaded_at: datetime = Column(DateTime, server_default=func.now())

    report = relationship("Report", back_populates="photos")

    __table_args__ = (
        Index('idx_report_photos_report_id', 'report_id'),
    )
