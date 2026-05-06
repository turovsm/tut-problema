from typing import Optional
from uuid import UUID
import os
import shutil
import asyncio

from fastapi import UploadFile
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.database.models.report import ReportPhoto, Report
from app.infrastructure.storage import save_upload_file
from app.repositories.report_repository import ReportRepository
from app.repositories.vote_repository import VoteRepository
from app.schemas.report import IssueType, ReportUpdate
from app.utils.distance import calculate_distance_haversine


async def enrich_report_data(report: Report, db_session, current_user_id=None, vote_repo=None):
    point = await db_session.execute(
        select(func.ST_X(report.location), func.ST_Y(report.location))
    )
    lng, lat = point.first()

    setattr(report, "parsed_lng", lng)
    setattr(report, "parsed_lat", lat)

    user_vote = None
    if current_user_id and vote_repo:
        vote = await vote_repo.get_user_vote(current_user_id, report.id)
        if vote:
            user_vote = "confirm" if vote.is_confirm else "dismiss"

    setattr(report, "current_user_vote", user_vote)
    return report


class ReportService:
    def __init__(self, report_repo: ReportRepository, vote_repo: VoteRepository = None):
        self.report_repo = report_repo
        self.vote_repo = vote_repo

    async def _enrich_reports_bulk(self, reports: list[Report], current_user_id=None):
        if not reports:
            return reports

        for r in reports:
            shape = to_shape(r.location)
            r.parsed_lng = shape.x
            r.parsed_lat = shape.y
            r.current_user_vote = None

        if current_user_id and self.vote_repo:
            report_ids = [r.id for r in reports]
            votes_map = await self.vote_repo.get_user_votes_for_reports(current_user_id, report_ids)

            for r in reports:
                if r.id in votes_map:
                    r.current_user_vote = "confirm" if votes_map[r.id].is_confirm else "dismiss"

        return reports

    async def get_report_by_id(self, report_id: UUID, current_user_id=None):
        report = await self.report_repo.get_with_relations(report_id)
        if report:
            return await enrich_report_data(report, self.report_repo.db, current_user_id, self.vote_repo)
        return None

    async def get_reports_paginated(self, issue_type: Optional[IssueType], status_filter: Optional[str], limit: int,
                                    offset: int, current_user_id=None):
        query = select(Report).options(selectinload(Report.created_by), selectinload(Report.photos))
        if issue_type:
            query = query.where(Report.issue_type == issue_type)
        if status_filter:
            query = query.where(Report.status == status_filter)

        total = await self.report_repo.db.execute(select(func.count()).select_from(query.subquery()))
        paginated_query = query.order_by(Report.created_at.desc()).offset(offset).limit(limit)
        items = await self.report_repo.db.execute(paginated_query)
        reports = items.scalars().all()

        enriched_reports = await self._enrich_reports_bulk(reports, current_user_id)
        return enriched_reports, total.scalar()

    async def get_nearby_reports(self, lat: float, lon: float, radius: int, limit: int, current_user_id=None):
        point = f"POINT({lon} {lat})"
        query = select(Report).options(selectinload(Report.created_by), selectinload(Report.photos)).where(
            func.ST_DWithin(Report.location, func.ST_GeomFromText(point, 4326), radius)
        ).order_by(
            func.ST_Distance(Report.location, func.ST_GeomFromText(point, 4326))
        ).limit(limit)

        items = await self.report_repo.db.execute(query)
        reports = items.scalars().all()
        return await self._enrich_reports_bulk(reports, current_user_id)

    async def get_user_reports(self, user_id: UUID, limit: int, offset: int):
        query = select(Report).options(selectinload(Report.created_by), selectinload(Report.photos)).where(
            Report.created_by_id == user_id)
        total = await self.report_repo.db.execute(select(func.count()).select_from(query.subquery()))
        paginated_query = query.order_by(Report.created_at.desc()).offset(offset).limit(limit)
        items = await self.report_repo.db.execute(paginated_query)
        reports = items.scalars().all()
        enriched_reports = await self._enrich_reports_bulk(reports, current_user_id=user_id)
        return enriched_reports, total.scalar()

    async def create_report(
            self, user_id: UUID, title: str, description: str, issue_type: IssueType,
            loc_lng: float, loc_lat: float, user_lng: float, user_lat: float, files: list[UploadFile]
    ) -> Report:
        distance = calculate_distance_haversine(user_lat, user_lng, loc_lat, loc_lng)
        if distance > settings.MAX_REPORT_DISTANCE_METERS:
            raise ValueError(f"Distance {distance:.0f}m exceeds max allowed ({settings.MAX_REPORT_DISTANCE_METERS}m).")

        report_data = {
            "title": title,
            "description": description,
            "issue_type": issue_type,
            "location": from_shape(Point(loc_lng, loc_lat), srid=4326),
            "user_location": from_shape(Point(user_lng, user_lat), srid=4326),
            "created_by_id": user_id
        }

        report = await self.report_repo.create(report_data)

        for file in files:
            file_path = await save_upload_file(file, report.id)
            photo = ReportPhoto(report_id=report.id, file_name=file.filename, file_path=file_path)
            await self.report_repo.add_photo(photo)

        await self.report_repo.db.commit()
        await self.report_repo.db.refresh(report)
        return report

    async def update_report(self, report_id: UUID, user_id: UUID, user_role: str, update_data: ReportUpdate):
        report = await self.report_repo.get(report_id)
        if not report:
            raise ValueError("Report not found")
        if report.created_by_id != user_id and user_role not in ["moderator", "gov_org"]:
            raise PermissionError("Not enough permissions")

        if update_data.title is not None:
            report.title = update_data.title
        if update_data.description is not None:
            report.description = update_data.description
        if update_data.status is not None:
            report.status = update_data.status

        await self.report_repo.db.commit()
        return report

    async def delete_report(self, report_id: UUID, user_id: UUID, user_role: str):
        report = await self.report_repo.get_with_relations(report_id)
        if not report:
            raise ValueError("Report not found")
        if report.created_by_id != user_id and user_role not in ["moderator", "gov_org"]:
            raise PermissionError("Not enough permissions")

        def cleanup_files():
            for photo in report.photos:
                if os.path.exists(photo.file_path):
                    os.remove(photo.file_path)

            report_dir = os.path.join(settings.UPLOAD_DIR, str(report_id))
            if os.path.exists(report_dir):
                shutil.rmtree(report_dir, ignore_errors=True)

        await asyncio.to_thread(cleanup_files)

        await self.report_repo.delete(report_id)
        await self.report_repo.db.commit()