from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.application.dto.reports import ReportPhotoDTO
from app.domain.entities.user import User
from app.presentation.api.deps import (
    get_add_photo_use_case,
    get_current_verified_user,
    get_delete_photo_use_case,
    get_photo_use_case,
    get_resolution_photo_use_case,
)
from app.presentation.api.schemas.common import SuccessResponse
from app.presentation.api.schemas.reports import ReportPhotoResponse

router = APIRouter()


@router.post(
    "/reports/{report_id}/photos",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[ReportPhotoResponse],
)
async def upload_report_photo(
    report_id: UUID,
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_add_photo_use_case)],
):
    photo = await use_case.execute(
        ReportPhotoDTO(
            report_id=report_id,
            user_id=current_user.id,
            user_role=current_user.role,
            file=file,
        )
    )

    photo_url = f"/api/uploads/photos/{photo.id}"

    return SuccessResponse(
        data=ReportPhotoResponse(
            id=photo.id,
            file_name=photo.file_name,
            file_url=photo_url,
            uploaded_at=photo.uploaded_at,
        ),
        message="Photo uploaded successfully",
    )


@router.get("/photos/{photo_id}")
async def get_photo(
    photo_id: UUID, use_case: Annotated[Depends, Depends(get_photo_use_case)]
):
    photo_metadata = await use_case.execute(photo_id)

    return FileResponse(
        path=photo_metadata.file_path, filename=photo_metadata.file_name
    )


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: UUID,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    use_case: Annotated[Depends, Depends(get_delete_photo_use_case)],
):
    await use_case.execute(
        photo_id=photo_id, user_id=current_user.id, user_role=current_user.role
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/resolutions/{photo_id}")
async def get_resolution_photo(
    photo_id: UUID,
    use_case: Annotated[Depends, Depends(get_resolution_photo_use_case)],
):
    photo_metadata = await use_case.execute(photo_id)

    return FileResponse(
        path=photo_metadata.file_path, filename=photo_metadata.file_name
    )
