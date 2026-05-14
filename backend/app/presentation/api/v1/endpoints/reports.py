from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Response,
    UploadFile,
    status,
)

from app.application.dto.reports import (
    CreateReportDTO,
    NearbyReportsDTO,
    ReportFilterDTO,
    ResolveReportDTO,
    UpdateReportDTO,
)
from app.domain.entities.user import User
from app.presentation.api.deps import (
    get_create_report_use_case,
    get_current_verified_user,
    get_delete_report_use_case,
    get_get_reports_use_case,
    get_my_reports_use_case,
    get_nearby_reports_use_case,
    get_optional_current_user,
    get_report_by_id_use_case,
    get_resolve_report_use_case,
    get_update_report_use_case,
)
from app.presentation.api.schemas.common import SuccessResponse
from app.presentation.api.schemas.reports import (
    NearbyReportQuery,
    ReportCreateForm,
    ReportFilterQuery,
    ReportIdResponse,
    ReportItemsResponse,
    ReportListQuery,
    ReportListResponse,
    ReportResponse,
    ReportUpdate,
    ResolveReportForm,
)
from app.presentation.api.v1.mappers import ReportMapper

router = APIRouter()


@router.get("", response_model=SuccessResponse[ReportListResponse])
async def list_reports(
    use_case: Annotated[Depends, Depends(get_get_reports_use_case)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    data: ReportFilterQuery = Depends(),
):
    assignee_id = None
    if data.assigned_to_me and current_user:
        assignee_id = current_user.id

    reports, total = await use_case.execute(
        ReportFilterDTO(
            issue_type=data.issue_type,
            status_filter=data.status_filter,
            page=data.page,
            limit=data.limit,
            current_user_id=current_user.id if current_user else None,
            assignee_id=assignee_id,
        )
    )

    return SuccessResponse(
        data=ReportListResponse(
            items=[ReportMapper.to_report_response(r) for r in reports],
            total=total,
            page=data.page,
            limit=data.limit,
            has_next=data.page * data.limit < total,
        )
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[ReportIdResponse],
)
async def create_report(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_create_report_use_case)],
    data: Annotated[ReportCreateForm, Depends(ReportCreateForm.as_form)],
    files: list[UploadFile] = File(...),
):
    report = await use_case.execute(
        CreateReportDTO(
            title=data.title,
            description=data.description,
            issue_type=data.issue_type,
            location_lng=data.location_lng,
            location_lat=data.location_lat,
            user_location_lng=data.user_location_lng,
            user_location_lat=data.user_location_lat,
            creator_id=current_user.id,
            files=files,
        )
    )
    return SuccessResponse(
        data=ReportIdResponse(id=report.id),
        message="Report created successfully",
    )


@router.get("/nearby", response_model=SuccessResponse[ReportItemsResponse])
async def get_nearby_reports(
    use_case: Annotated[Depends, Depends(get_nearby_reports_use_case)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    data: NearbyReportQuery = Depends(),
):
    reports = await use_case.execute(
        NearbyReportsDTO(
            lat=data.lat,
            lon=data.lon,
            radius=data.radius,
            limit=data.limit,
            current_user_id=current_user.id if current_user else None,
        )
    )
    return SuccessResponse(
        data=ReportItemsResponse(
            items=[ReportMapper.to_report_response(r) for r in reports]
        )
    )


@router.get("/user/me", response_model=SuccessResponse[ReportListResponse])
async def get_my_reports(
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_my_reports_use_case)],
    data: ReportListQuery = Depends(),
):
    reports, total = await use_case.execute(
        current_user.id, data.page, data.limit
    )
    return SuccessResponse(
        data=ReportListResponse(
            items=[ReportMapper.to_report_response(r) for r in reports],
            total=total,
            page=data.page,
            limit=data.limit,
            has_next=data.page * data.limit < total,
        )
    )


@router.get("/{report_id}", response_model=SuccessResponse[ReportResponse])
async def get_report(
    report_id: UUID,
    use_case: Annotated[Depends, Depends(get_report_by_id_use_case)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
):
    report = await use_case.execute(
        report_id, current_user.id if current_user else None
    )
    return SuccessResponse(data=ReportMapper.to_report_response(report))


@router.put("/{report_id}", response_model=SuccessResponse[ReportResponse])
async def update_report(
    report_id: UUID,
    data: ReportUpdate,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_update_report_use_case)],
):
    report = await use_case.execute(
        UpdateReportDTO(
            report_id=report_id,
            user_id=current_user.id,
            user_role=current_user.role,
            title=data.title,
            description=data.description,
            status=data.status,
            assigned_to_id=data.assigned_to_id,
        )
    )
    return SuccessResponse(
        data=ReportMapper.to_report_response(report),
        message="Report updated successfully",
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_delete_report_use_case)],
):
    await use_case.execute(report_id, current_user.id, current_user.role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{report_id}/resolve", status_code=status.HTTP_201_CREATED)
async def resolve_report(
    report_id: UUID,
    form_data: Annotated[
        ResolveReportForm, Depends(ResolveReportForm.as_form)
    ],
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_resolve_report_use_case)],
    files: list[UploadFile] = File(default=[]),
):
    await use_case.execute(
        ResolveReportDTO(
            report_id=report_id,
            resolved_by_id=current_user.id,
            comment=form_data.comment,
            files=files,
        )
    )
    return SuccessResponse(message="Report successfully resolved")
