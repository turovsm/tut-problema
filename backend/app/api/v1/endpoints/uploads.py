import os
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select, func

from app.api.deps import get_current_verified_user, get_report_repo
from app.core.config import settings
from app.database.models.report import ReportPhoto
from app.database.models.user import User
from app.infrastructure.storage import save_upload_file
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportPhotoResponse

router = APIRouter()


@router.post("/reports/{report_id}/photos", response_model=ReportPhotoResponse)
async def upload_report_photo(
        report_id: UUID,
        file: UploadFile = File(...),
        current_user: Annotated[User, Depends(get_current_verified_user)] = None,
        report_repo: Annotated[ReportRepository, Depends(get_report_repo)] = None
):
    report = await report_repo.get(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.created_by_id != current_user.id and current_user.role not in ["moderator", "gov_org"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    # Count existing photos
    existing_photos = await report_repo.db.execute(
        select(func.count()).where(ReportPhoto.report_id == report_id)
    )
    photo_count = existing_photos.scalar()
    if photo_count >= settings.MAX_PHOTOS_PER_REPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.MAX_PHOTOS_PER_REPORT} photos per report. This report already has {photo_count} photos."
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    try:
        file_path = await save_upload_file(file, report_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    photo = ReportPhoto(report_id=report_id, file_name=file.filename, file_path=file_path)
    await report_repo.add_photo(photo)
    await report_repo.db.commit()
    await report_repo.db.refresh(photo)

    return ReportPhotoResponse(
        id=photo.id,
        file_name=file.filename,
        file_url=f"{settings.PHOTO_URL_PREFIX}/{photo.id}",
        uploaded_at=photo.uploaded_at
    )


@router.get("/photos/{photo_id}")
async def get_photo(
        photo_id: UUID,
        report_repo: Annotated[ReportRepository, Depends(get_report_repo)]
):
    result = await report_repo.db.execute(select(ReportPhoto).where(ReportPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo or not os.path.exists(photo.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return FileResponse(photo.file_path)


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
        photo_id: UUID,
        current_user: Annotated[User, Depends(get_current_verified_user)],
        report_repo: Annotated[ReportRepository, Depends(get_report_repo)]
):
    result = await report_repo.db.execute(select(ReportPhoto).where(ReportPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    report = await report_repo.get(photo.report_id)
    if report.created_by_id != current_user.id and current_user.role not in ["moderator", "gov_org"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    # Check minimum photos constraint
    remaining_photos = await report_repo.db.execute(
        select(func.count()).where(ReportPhoto.report_id == photo.report_id)
    )
    if remaining_photos.scalar() <= settings.MIN_PHOTOS_PER_REPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete the last photo. Reports must have at least {settings.MIN_PHOTOS_PER_REPORT} photo(s)."
        )

    if os.path.exists(photo.file_path):
        os.remove(photo.file_path)

    await report_repo.db.delete(photo)
    await report_repo.db.commit()
    return None
