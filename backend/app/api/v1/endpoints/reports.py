from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.api.deps import (
    get_current_active_user,
    get_current_verified_user,
    get_optional_current_user,
    get_report_service,
)
from app.core.config import settings
from app.database.models.report import Report
from app.database.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.report import (
    IssueType,
    ReportIdResponse,
    ReportItemsResponse,
    ReportListResponse,
    ReportPhotoResponse,
    ReportResponse,
    ReportStatus,
    ReportUpdate,
)
from app.services.report_service import ReportService

router = APIRouter()


def map_report_to_schema(report: Report) -> ReportResponse:
    photos = [
        ReportPhotoResponse(
            id=p.id,
            file_name=p.file_name,
            file_url=f"{settings.PHOTO_URL_PREFIX}/{p.id}",
            uploaded_at=p.uploaded_at,
        )
        for p in report.photos
    ]
    created_by = {
        "id": report.created_by.id,
        "username": report.created_by.username,
        "role": report.created_by.role,
        "email": report.created_by.email,
        "is_active": report.created_by.is_active,
        "is_verified": report.created_by.is_verified,
        "created_at": report.created_by.created_at,
    }
    return ReportResponse(
        id=report.id,
        title=report.title,
        description=report.description,
        issue_type=report.issue_type,
        location={
            "type": "Point",
            "coordinates": [report.parsed_lng, report.parsed_lat],
        },
        status=report.status,
        created_by=created_by,
        created_at=report.created_at,
        updated_at=report.updated_at,
        photos=photos,
        user_vote=getattr(report, "current_user_vote", None),
    )


@router.get("", response_model=ReportListResponse)
async def list_reports(
    report_service: Annotated[ReportService, Depends(get_report_service)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    issue_type: Optional[IssueType] = None,
    status_filter: Optional[ReportStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE
    ),
):
    offset = (page - 1) * limit
    reports, total = await report_service.get_reports_paginated(
        issue_type, status_filter, limit, offset, current_user.id
    )
    return ReportListResponse(
        items=[map_report_to_schema(r) for r in reports],
        total=total,
        page=page,
        limit=limit,
        has_next=page * limit < total,
    )


@router.get("/nearby", response_model=SuccessResponse[ReportItemsResponse])
async def get_nearby_reports(
    report_service: Annotated[ReportService, Depends(get_report_service)],
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)],
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: int = Query(
        settings.DEFAULT_RADIUS_METERS,
        ge=settings.MIN_RADIUS_METERS,
        le=settings.MAX_RADIUS_METERS,
    ),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=settings.MIN_PAGE_SIZE,
        le=settings.MAX_PAGE_SIZE,
    ),
):
    user_id = current_user.id if current_user else None
    reports = await report_service.get_nearby_reports(
        lat, lon, radius, limit, user_id
    )
    return SuccessResponse(
        data={"items": [map_report_to_schema(r) for r in reports]}
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[ReportIdResponse],
)
async def create_report(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    title: str = Form(...),
    description: Optional[str] = Form(None),
    issue_type: IssueType = Form(...),
    location_lng: float = Form(...),
    location_lat: float = Form(...),
    user_location_lng: float = Form(...),
    user_location_lat: float = Form(...),
    files: List[UploadFile] = File(...),
):
    if (
        len(title) < settings.REPORT_TITLE_MIN_LENGTH
        or len(title) > settings.REPORT_TITLE_MAX_LENGTH
    ):
        raise HTTPException(status_code=400, detail="Title length invalid")
    if (
        description
        and len(description) > settings.REPORT_DESCRIPTION_MAX_LENGTH
    ):
        raise HTTPException(status_code=400, detail="Description too long")
    if (
        len(files) < settings.MIN_PHOTOS_PER_REPORT
        or len(files) > settings.MAX_PHOTOS_PER_REPORT
    ):
        raise HTTPException(status_code=400, detail="Invalid photo count")
    if not (-180 <= location_lng <= 180) or not (-90 <= location_lat <= 90):
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    try:
        report = await report_service.create_report(
            current_user.id,
            title,
            description,
            issue_type,
            location_lng,
            location_lat,
            user_location_lng,
            user_location_lat,
            files,
        )
        return SuccessResponse(
            data={"id": report.id}, message="Report created successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/user/me", response_model=ReportListResponse)
async def get_my_reports(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    page: int = Query(1, ge=1),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE
    ),
):
    offset = (page - 1) * limit
    reports, total = await report_service.get_user_reports(
        current_user.id, limit, offset
    )
    return ReportListResponse(
        items=[map_report_to_schema(r) for r in reports],
        total=total,
        page=page,
        limit=limit,
        has_next=page * limit < total,
    )


@router.get("/{report_id}", response_model=SuccessResponse[ReportResponse])
async def get_report(
    report_id: UUID,
    report_service: Annotated[ReportService, Depends(get_report_service)],
    current_user: Annotated[Optional[User], Depends(get_optional_current_user)],
):
    user_id = current_user.id if current_user else None
    report = await report_service.get_report_by_id(report_id, user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return SuccessResponse(data=map_report_to_schema(report))


@router.put("/{report_id}", response_model=SuccessResponse[None])
async def update_report(
    report_id: UUID,
    report_data: ReportUpdate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
):
    try:
        await report_service.update_report(
            report_id, current_user.id, current_user.role, report_data
        )
        return SuccessResponse(message="Report updated successfully")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
):
    try:
        await report_service.delete_report(
            report_id, current_user.id, current_user.role
        )
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
