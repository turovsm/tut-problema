import os
import aiofiles
from datetime import datetime
from uuid import UUID

from fastapi import UploadFile

from app.core.config import settings


async def save_upload_file(upload_file: UploadFile, report_id: UUID) -> str:
    safe_filename = os.path.basename(upload_file.filename)
    file_ext = safe_filename.split('.')[-1].lower()

    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}")

    report_dir = os.path.join(settings.UPLOAD_DIR, str(report_id))
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{upload_file.filename}"
    file_path = os.path.join(report_dir, unique_filename)

    async with aiofiles.open(file_path, "wb") as buffer:
        while chunk := await upload_file.read(8192):
            await buffer.write(chunk)

    return file_path
