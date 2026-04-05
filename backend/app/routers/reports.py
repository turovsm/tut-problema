from typing import Annotated, Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query, File, UploadFile, Form
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import Report, User as UserModel, Vote, ReportPhoto
from app.database import get_db
from app.dependencies import get_current_active_user, get_current_verified_user
from app.logging_config import get_logger
from app.routers.uploads import save_upload_file
from app.schemas import (
    ReportUpdate, Report as ReportSchema,
    ReportListResponse, SuccessResponse, IssueType, ReportStatus, VoteType,
    User as UserSchema, ReportPhotoResponse, Location
)
from app.utils.distance import calculate_distance_haversine

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = get_logger("app.routers.reports")

POINT_PREFIX = "POINT("
POINT_SUFFIX = ")"
REPORT_NOT_FOUND = "Report not found"

DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[UserModel, Depends(get_current_active_user)]
VerifiedUser = Annotated[UserModel, Depends(get_current_verified_user)]
OptionalCurrentUser = Annotated[Optional[UserModel], Depends(get_current_active_user)]


def parse_point_coordinates(point_text: str) -> tuple[float, float]:
    coords = point_text.replace(POINT_PREFIX, "").replace(POINT_SUFFIX, "").split()
    return float(coords[0]), float(coords[1])


async def get_photo_responses(photos: list[ReportPhoto]) -> list[ReportPhotoResponse]:
    return [
        ReportPhotoResponse(
            id=photo.id,
            file_name=photo.file_name,
            file_url=f"{settings.PHOTO_URL_PREFIX}/{photo.id}",
            uploaded_at=photo.uploaded_at
        )
        for photo in photos
    ]


async def get_user_vote(current_user: Optional[UserModel], report_id: UUID, db: AsyncSession) -> Optional[VoteType]:
    if not current_user:
        return None
    vote = await db.scalar(
        select(Vote).where(
            Vote.user_id == current_user.id,
            Vote.report_id == report_id
        )
    )
    if not vote:
        return None
    return VoteType.CONFIRM if vote.is_confirm else VoteType.DISMISS


async def build_report_schema(report: Report, current_user: Optional[UserModel],
                              db: AsyncSession) -> ReportSchema:
    point_text = await db.scalar(select(report.location.ST_AsText()))
    lng, lat = parse_point_coordinates(point_text)
    user_vote = await get_user_vote(current_user, report.id, db)

    result = await db.execute(select(ReportPhoto).where(ReportPhoto.report_id == report.id))
    photos = result.scalars().all()
    photo_responses = await get_photo_responses(photos)

    return ReportSchema(
        id=report.id,
        title=report.title,
        description=report.description,
        issue_type=report.issue_type,
        location={"type": "Point", "coordinates": [lng, lat]},
        address=None,
        status=report.status,
        created_by=UserSchema.model_validate(report.created_by),
        created_at=report.created_at,
        updated_at=report.updated_at,
        photos=photo_responses,
        user_vote=user_vote
    )


@router.get("", response_model=ReportListResponse)
async def list_reports(
        db: DBSession,
        current_user: CurrentUser,
        issue_type: Optional[IssueType] = None,
        status_filter: Optional[ReportStatus] = None,
        page: int = Query(1, ge=1),
        limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE)
):
    query = select(Report).options(selectinload(Report.created_by))

    if issue_type:
        query = query.where(Report.issue_type == issue_type)
    if status_filter:
        query = query.where(Report.status == status_filter)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(Report.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    items = []
    for report in reports:
        items.append(await build_report_schema(report, current_user, db))

    return ReportListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=page * limit < total
    )


@router.get("/nearby")
async def get_nearby_reports(
        db: DBSession,
        current_user: CurrentUser,
        lat: float = Query(..., ge=-90, le=90),
        lon: float = Query(..., ge=-180, le=180),
        radius: int = Query(settings.DEFAULT_RADIUS_METERS, ge=settings.MIN_RADIUS_METERS,
                            le=settings.MAX_RADIUS_METERS),
        limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=settings.MIN_PAGE_SIZE, le=settings.MAX_PAGE_SIZE)
):
    point = f"{POINT_PREFIX}{lon} {lat}{POINT_SUFFIX}"

    query = select(Report).options(selectinload(Report.created_by)).where(
        func.ST_DWithin(Report.location, func.ST_GeomFromText(point, 4326), radius)
    ).order_by(
        func.ST_Distance(Report.location, func.ST_GeomFromText(point, 4326))
    ).limit(limit)

    result = await db.execute(query)
    reports = result.scalars().all()

    items = []
    for report in reports:
        items.append(await build_report_schema(report, current_user, db))

    return SuccessResponse(data={"items": [item.model_dump() for item in items]})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_report(
        db: DBSession,
        current_user: VerifiedUser,
        title: str = Form(...),
        description: Optional[str] = Form(None),
        issue_type: IssueType = Form(...),
        location_lng: float = Form(...),
        location_lat: float = Form(...),
        user_location_lng: float = Form(...),
        user_location_lat: float = Form(...),
        files: List[UploadFile] = File(...),
):
    if len(title) < settings.REPORT_TITLE_MIN_LENGTH or len(title) > settings.REPORT_TITLE_MAX_LENGTH:
        raise HTTPException(status_code=400,
                            detail=f"Title must be between {settings.REPORT_TITLE_MIN_LENGTH} and {settings.REPORT_TITLE_MAX_LENGTH} characters")

    if description and len(description) > settings.REPORT_DESCRIPTION_MAX_LENGTH:
        raise HTTPException(status_code=400,
                            detail=f"Description cannot exceed {settings.REPORT_DESCRIPTION_MAX_LENGTH} characters")

    if len(files) < settings.MIN_PHOTOS_PER_REPORT or len(files) > settings.MAX_PHOTOS_PER_REPORT:
        raise HTTPException(status_code=400,
                            detail=f"Number of photos must be between {settings.MIN_PHOTOS_PER_REPORT} and {settings.MAX_PHOTOS_PER_REPORT}")

    if not (-180 <= location_lng <= 180):
        raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
    if not (-90 <= location_lat <= 90):
        raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
    if not (-180 <= user_location_lng <= 180):
        raise HTTPException(status_code=400, detail="User longitude must be between -180 and 180")
    if not (-90 <= user_location_lat <= 90):
        raise HTTPException(status_code=400, detail="User latitude must be between -90 and 90")

    logger.info(
        "Creating new report",
        user_id=str(current_user.id),
        title=title,
        issue_type=issue_type,
        photo_count=len(files)
    )

    location = Location(type="Point", coordinates=[location_lng, location_lat])
    user_location = Location(type="Point", coordinates=[user_location_lng, user_location_lat])

    report_lng, report_lat = location.coordinates
    user_lng, user_lat = user_location.coordinates

    distance = calculate_distance_haversine(
        user_lat, user_lng,
        report_lat, report_lng
    )

    if distance > settings.MAX_REPORT_DISTANCE_METERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot report issue {distance:.0f} meters away. Maximum allowed distance is {settings.MAX_REPORT_DISTANCE_METERS} meters."
        )

    report_point = Point(report_lng, report_lat)
    user_point = Point(user_lng, user_lat)

    report = Report(
        title=title,
        description=description,
        issue_type=issue_type,
        location=from_shape(report_point, srid=4326),
        user_location=from_shape(user_point, srid=4326),
        created_by_id=current_user.id
    )
    db.add(report)
    await db.flush()

    for file in files:
        file_path = await save_upload_file(file, report.id)
        photo = ReportPhoto(report_id=report.id, file_name=file.filename, file_path=file_path)
        db.add(photo)

    await db.commit()
    await db.refresh(report)

    logger.info("Report created successfully", report_id=str(report.id), user_id=str(current_user.id))

    return SuccessResponse(
        data={"id": str(report.id)},
        message=f"Report created successfully with {len(files)} photo(s)"
    )


@router.get("/{report_id}")
async def get_report(
        report_id: UUID,
        db: DBSession,
        current_user: OptionalCurrentUser
):
    query = select(Report).options(selectinload(Report.created_by)).where(Report.id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=REPORT_NOT_FOUND)

    report_schema = await build_report_schema(report, current_user, db)

    return SuccessResponse(data=report_schema.model_dump())


@router.put("/{report_id}")
async def update_report(
        report_id: UUID,
        report_data: ReportUpdate,
        db: DBSession,
        current_user: VerifiedUser
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=REPORT_NOT_FOUND)

    if report.created_by_id != current_user.id and current_user.role not in ["moderator", "gov_org"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    if report_data.title is not None:
        report.title = report_data.title
    if report_data.description is not None:
        report.description = report_data.description
    if report_data.status is not None:
        report.status = report_data.status

    await db.commit()
    return SuccessResponse(message="Report updated successfully")


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
        report_id: UUID,
        db: DBSession,
        current_user: VerifiedUser
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=REPORT_NOT_FOUND)

    if report.created_by_id != current_user.id and current_user.role not in ["moderator", "gov_org"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    await db.delete(report)
    await db.commit()

    logger.warning("Report deleted", report_id=str(report_id), user_id=str(current_user.id))

    return None


@router.get("/user/me")
async def get_my_reports(
        db: DBSession,
        current_user: VerifiedUser,
        page: int = Query(1, ge=1),
        limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE)
):
    query = select(Report).where(Report.created_by_id == current_user.id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(Report.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    items = []
    for report in reports:
        point_text = await db.scalar(select(report.location.ST_AsText()))
        lng, lat = parse_point_coordinates(point_text)
        items.append(ReportSchema(
            id=report.id,
            title=report.title,
            description=report.description,
            issue_type=report.issue_type,
            location={"type": "Point", "coordinates": [lng, lat]},
            address=None,
            status=report.status,
            created_by=UserSchema.model_validate(current_user),
            created_at=report.created_at,
            updated_at=report.updated_at,
            photos=[],
            user_vote=None
        ))

    return ReportListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=page * limit < total
    )
