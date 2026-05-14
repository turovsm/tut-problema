from uuid import UUID

from geoalchemy2.functions import ST_Distance, ST_DWithin
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import delete, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.location import Location
from app.domain.entities.report import (
    Report,
    ReportPhoto,
    ReportResolution,
    ResolutionPhoto,
)
from app.domain.entities.user import User
from app.domain.interfaces.repositories.report_repository import (
    IReportRepository,
)
from app.infrastructure.database.models import (
    ReportModel,
    ReportPhotoModel,
    ReportResolutionModel,
    ResolutionPhotoModel,
)
from app.infrastructure.database.repositories.base import (
    BaseSQLAlchemyRepository,
)


class ReportRepository(
    BaseSQLAlchemyRepository[ReportModel], IReportRepository
):
    def __init__(self, session: AsyncSession):
        super().__init__(ReportModel, session)

    def _to_domain_location(self, wkb_element) -> Location:
        shape = to_shape(wkb_element)
        return Location(longitude=shape.x, latitude=shape.y)

    def _to_domain(self, model: ReportModel) -> Report:
        report = Report(
            id=model.id,
            title=model.title,
            description=model.description,
            issue_type=model.issue_type,
            location=self._to_domain_location(model.location),
            user_location=self._to_domain_location(model.user_location),
            status=model.status,
            created_by_id=model.created_by_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        state = inspect(model)
        if "photos" not in state.unloaded:
            report.photos = [
                ReportPhoto(
                    id=p.id,
                    report_id=p.report_id,
                    file_name=p.file_name,
                    file_path=p.file_path,
                    uploaded_at=p.uploaded_at,
                )
                for p in model.photos
            ]
        else:
            report.photos = []

        if "creator" not in state.unloaded and model.creator:
            report.created_by = User(
                id=model.creator.id,
                email=model.creator.email,
                username=model.creator.username,
                password_hash=model.creator.password_hash,
                role=model.creator.role,
                is_active=model.creator.is_active,
                is_verified=model.creator.is_verified,
                created_at=model.creator.created_at,
            )
        else:
            report.created_by = None

        if "assignee" not in state.unloaded and model.assignee:
            report.assigned_to = User(
                id=model.assignee.id,
                email=model.assignee.email,
                username=model.assignee.username,
                password_hash=model.assignee.password_hash,
                role=model.assignee.role,
                is_active=model.assignee.is_active,
                is_verified=model.assignee.is_verified,
                created_at=model.assignee.created_at,
            )
            report.assigned_to_id = model.assignee.id
        else:
            report.assigned_to = None
            report.assigned_to_id = model.assigned_to_id

        if "resolution" not in state.unloaded and model.resolution:
            res_state = inspect(model.resolution)
            res_photos = []
            if "photos" not in res_state.unloaded:
                res_photos = [
                    ResolutionPhoto(
                        id=p.id,
                        resolution_id=p.resolution_id,
                        file_name=p.file_name,
                        file_path=p.file_path,
                        uploaded_at=p.uploaded_at,
                    )
                    for p in model.resolution.photos
                ]
            report.resolution = ReportResolution(
                id=model.resolution.id,
                report_id=model.resolution.report_id,
                resolved_by_id=model.resolution.resolved_by_id,
                comment=model.resolution.comment,
                resolved_at=model.resolution.resolved_at,
                photos=res_photos,
            )
        else:
            report.resolution = None
        return report

    async def get_by_id(self, report_id: UUID) -> Report | None:
        query = (
            select(self._model)
            .options(
                selectinload(self._model.photos),
                selectinload(self._model.creator),
                selectinload(self._model.assignee),
                selectinload(self._model.resolution).selectinload(
                    ReportResolutionModel.photos
                ),
            )
            .where(self._model.id == report_id)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, report: Report) -> Report:
        query = (
            select(self._model)
            .options(
                selectinload(self._model.creator),
                selectinload(self._model.assignee),
            )
            .where(self._model.id == report.id)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        loc_wkb = from_shape(
            Point(report.location.longitude, report.location.latitude),
            srid=4326,
        )
        u_loc_wkb = from_shape(
            Point(
                report.user_location.longitude, report.user_location.latitude
            ),
            srid=4326,
        )

        if not model:
            model = ReportModel(
                id=report.id,
                title=report.title,
                description=report.description,
                issue_type=report.issue_type,
                location=loc_wkb,
                user_location=u_loc_wkb,
                status=report.status,
                created_by_id=report.created_by_id,
                created_at=report.created_at,
                assigned_to_id=report.assigned_to_id,
            )
            self._session.add(model)
        else:
            model.title = report.title
            model.description = report.description
            model.status = report.status
            model.updated_at = report.updated_at
            model.assigned_to_id = report.assigned_to_id

        await self._session.flush()
        await self._session.refresh(
            model, ["creator", "assignee", "updated_at"]
        )
        await self._session.commit()
        return self._to_domain(model)

    async def delete(self, report_id: UUID) -> None:
        query = select(self._model).where(self._model.id == report_id)
        res = await self._session.execute(query)
        model = res.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.commit()

    async def get_list(
        self,
        issue_type=None,
        status=None,
        assignee_id=None,
        limit=20,
        offset=0,
    ) -> tuple[list[Report], int]:
        query = select(self._model).options(
            selectinload(self._model.photos),
            selectinload(self._model.creator),
            selectinload(self._model.assignee),
            selectinload(self._model.resolution).selectinload(
                ReportResolutionModel.photos
            ),
        )
        if issue_type:
            query = query.where(self._model.issue_type == issue_type)
        if status:
            query = query.where(self._model.status == status)
        if assignee_id:
            query = query.where(self._model.assigned_to_id == assignee_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self._session.execute(count_query)

        query = (
            query.order_by(self._model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(query)

        return [
            self._to_domain(m) for m in result.scalars().all()
        ], total.scalar()

    async def get_nearby(
        self, lat: float, lon: float, radius_meters: int, limit: int
    ) -> list[Report]:
        point_wkb = from_shape(Point(lon, lat), srid=4326)
        query = (
            select(self._model)
            .options(
                selectinload(self._model.photos),
                selectinload(self._model.creator),
            )
            .where(ST_DWithin(self._model.location, point_wkb, radius_meters))
            .order_by(ST_Distance(self._model.location, point_wkb))
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_user(
        self, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[Report], int]:
        query = (
            select(self._model)
            .options(
                selectinload(self._model.photos),
                selectinload(self._model.creator),
            )
            .where(self._model.created_by_id == user_id)
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.order_by(self._model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(query)

        return [self._to_domain(m) for m in result.scalars().all()], total

    async def add_photo(self, photo: ReportPhoto) -> ReportPhoto:
        model = ReportPhotoModel(
            id=photo.id,
            report_id=photo.report_id,
            file_name=photo.file_name,
            file_path=photo.file_path,
            uploaded_at=photo.uploaded_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return photo

    async def get_photo_by_id(self, photo_id: UUID) -> ReportPhoto | None:
        query = select(ReportPhotoModel).where(ReportPhotoModel.id == photo_id)
        res = await self._session.execute(query)
        m = res.scalar_one_or_none()
        return (
            ReportPhoto(
                id=m.id,
                report_id=m.report_id,
                file_name=m.file_name,
                file_path=m.file_path,
                uploaded_at=m.uploaded_at,
            )
            if m
            else None
        )

    async def delete_photo(self, photo_id: UUID) -> None:
        query = select(ReportPhotoModel).where(ReportPhotoModel.id == photo_id)
        res = await self._session.execute(query)
        m = res.scalar_one_or_none()
        if m:
            await self._session.delete(m)
            await self._session.commit()

    async def save_resolution(
        self, resolution: ReportResolution
    ) -> ReportResolution:
        model = ReportResolutionModel(
            id=resolution.id,
            report_id=resolution.report_id,
            resolved_by_id=resolution.resolved_by_id,
            comment=resolution.comment,
            resolved_at=resolution.resolved_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return resolution

    async def add_resolution_photo(
        self, photo: ResolutionPhoto
    ) -> ResolutionPhoto:
        model = ResolutionPhotoModel(
            id=photo.id,
            resolution_id=photo.resolution_id,
            file_name=photo.file_name,
            file_path=photo.file_path,
            uploaded_at=photo.uploaded_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return photo

    async def get_resolution_photo_by_id(
        self, photo_id: UUID
    ) -> ResolutionPhoto | None:
        query = select(ResolutionPhotoModel).where(
            ResolutionPhotoModel.id == photo_id
        )
        res = await self._session.execute(query)
        m = res.scalar_one_or_none()
        return (
            ResolutionPhoto(
                id=m.id,
                resolution_id=m.resolution_id,
                file_name=m.file_name,
                file_path=m.file_path,
                uploaded_at=m.uploaded_at,
            )
            if m
            else None
        )

    async def get_resolution_by_id(
        self, resolution_id: UUID
    ) -> ReportResolution | None:
        query = (
            select(ReportResolutionModel)
            .options(selectinload(ReportResolutionModel.photos))
            .where(ReportResolutionModel.id == resolution_id)
        )
        res = await self._session.execute(query)
        m = res.scalar_one_or_none()

        if not m:
            return None

        return ReportResolution(
            id=m.id,
            report_id=m.report_id,
            resolved_by_id=m.resolved_by_id,
            comment=m.comment,
            resolved_at=m.resolved_at,
            photos=[
                ResolutionPhoto(
                    id=p.id,
                    resolution_id=p.resolution_id,
                    file_name=p.file_name,
                    file_path=p.file_path,
                    uploaded_at=p.uploaded_at,
                )
                for p in m.photos
            ],
        )

    async def delete_resolution_photo(self, photo_id: UUID) -> None:
        query = delete(ResolutionPhotoModel).where(
            ResolutionPhotoModel.id == photo_id
        )
        await self._session.execute(query)
        await self._session.commit()

    async def delete_resolution_by_report_id(self, report_id: UUID) -> None:
        query = delete(ReportResolutionModel).where(
            ReportResolutionModel.report_id == report_id
        )
        await self._session.execute(query)
        await self._session.commit()
