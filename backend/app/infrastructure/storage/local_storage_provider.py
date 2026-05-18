import os
import shutil
from datetime import datetime
from typing import Any

import aiofiles

from app.core.config import settings
from app.domain.interfaces.providers.storage_provider import IStorageProvider


class LocalStorageProvider(IStorageProvider):
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS

    async def save_file(self, file: Any, subfolder: str) -> str:
        filename = getattr(file, "filename", "unknown.jpg")
        extension = filename.split(".")[-1].lower() if "." in filename else ""

        if extension not in self.allowed_extensions:
            raise ValueError(
                f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
            )

        target_dir = os.path.join(self.upload_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{timestamp}_{filename}"
        file_path = os.path.join(target_dir, unique_name)

        async with aiofiles.open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                await buffer.write(chunk)

        await file.seek(0)

        return file_path

    async def delete_file(self, file_path: str) -> None:
        if os.path.exists(file_path):
            os.remove(file_path)
            report_dir = os.path.dirname(file_path)
            if os.path.isdir(report_dir) and not os.listdir(report_dir):
                shutil.rmtree(report_dir, ignore_errors=True)
