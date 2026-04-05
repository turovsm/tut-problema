import os
import shutil
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, Report, ReportPhoto
from app.dependencies import get_current_verified_user
from app.logging_config import get_logger
from app.schemas import PhotoUploadResponse

router = APIRouter(prefix="/uploads", tags=["Uploads"])
logger = get_logger("app.routers.uploads")


async def save_upload_file(upload_file: UploadFile, report_id: UUID) -> str:
    file_ext = upload_file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    report_dir = os.path.join(settings.UPLOAD_DIR, str(report_id))
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{upload_file.filename}"
    file_path = os.path.join(report_dir, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    return file_path


@router.post("/reports/{report_id}/photos", response_model=PhotoUploadResponse)
async def upload_report_photo(
        report_id: UUID,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_verified_user)
):
    logger.info(
        "Photo upload attempted",
        user_id=str(current_user.id),
        report_id=str(report_id),
        filename=file.filename
    )
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    if report.created_by_id != current_user.id and current_user.role not in ["moderator", "gov_org"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add photos to your own reports"
        )

    photo_count_result = await db.execute(
        select(func.count()).where(ReportPhoto.report_id == report_id)
    )
    existing_photos = photo_count_result.scalar()

    if existing_photos >= settings.MAX_PHOTOS_PER_REPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.MAX_PHOTOS_PER_REPORT} photos per report. This report already has {existing_photos} photos."
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    file_path = await save_upload_file(file, report_id)

    photo = ReportPhoto(
        report_id=report_id,
        file_name=file.filename,
        file_path=file_path
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    file_url = f"{settings.PHOTO_URL_PREFIX}/{photo.id}"

    logger.info("Photo uploaded successfully", photo_id=str(photo.id))

    return PhotoUploadResponse(
        id=photo.id,
        file_name=file.filename,
        file_url=file_url,
        uploaded_at=photo.uploaded_at
    )


@router.get("/photos/{photo_id}")
async def get_photo(
        photo_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ReportPhoto).where(ReportPhoto.id == photo_id))
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    if not os.path.exists(photo.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo file not found on server"
        )

    return FileResponse(photo.file_path)


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
        photo_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_verified_user)
):
    result = await db.execute(select(ReportPhoto).where(ReportPhoto.id == photo_id))
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    report_result = await db.execute(select(Report).where(Report.id == photo.report_id))
    report = report_result.scalar_one_or_none()

    if report.created_by_id != current_user.id and current_user.role not in ["moderator", "gov_org"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    photo_count_result = await db.execute(
        select(func.count()).where(ReportPhoto.report_id == photo.report_id)
    )
    photo_count = photo_count_result.scalar()

    if photo_count <= settings.MIN_PHOTOS_PER_REPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete the last photo. Reports must have at least {settings.MIN_PHOTOS_PER_REPORT} photo(s)."
        )

    if os.path.exists(photo.file_path):
        os.remove(photo.file_path)

    await db.delete(photo)
    await db.commit()

    logger.warning("Photo deleted", photo_id=str(photo_id), user_id=str(current_user.id))

    return None
