import os
from unittest.mock import MagicMock

import pytest

from app.core.config import settings
from app.infrastructure.storage.local_storage_provider import (
    LocalStorageProvider,
)


class TestLocalStorageProviderIntegration:
    @pytest.fixture
    def provider(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
        return LocalStorageProvider()

    def create_mock_file(self, filename: str, content: bytes):
        mock_file = MagicMock()
        mock_file.filename = filename
        state = {"already_read": False}

        async def mock_read(size=-1):
            if state["already_read"]:
                return b""
            state["already_read"] = True
            return content

        async def mock_seek(offset):
            if offset == 0:
                state["already_read"] = False

        mock_file.read = mock_read
        mock_file.seek = mock_seek
        return mock_file

    async def test_save_file_success(self, provider):
        report_id = "test-report-uuid"
        file_content = b"fake-image-binary-data"
        mock_file = self.create_mock_file("pothole.jpg", file_content)

        saved_path = await provider.save_file(mock_file, subfolder=report_id)

        assert os.path.exists(saved_path)
        assert report_id in saved_path
        assert saved_path.endswith(".jpg")

        with open(saved_path, "rb") as f:
            assert f.read() == file_content

    async def test_save_file_invalid_extension(self, provider):
        mock_file = self.create_mock_file("virus.exe", b"malware")

        with pytest.raises(ValueError) as exc:
            await provider.save_file(mock_file, subfolder="any")

        assert "File type not allowed" in str(exc.value)

    async def test_delete_file_and_cleanup_folder(self, provider):
        report_id = "cleanup-test"
        mock_file = self.create_mock_file("to_delete.png", b"data")

        file_path = await provider.save_file(mock_file, subfolder=report_id)
        report_dir = os.path.dirname(file_path)

        assert os.path.exists(file_path)

        await provider.delete_file(file_path)

        assert not os.path.exists(file_path)
        assert not os.path.exists(report_dir)

    async def test_delete_file_keeps_folder_if_not_empty(self, provider):
        report_id = "keep-folder-test"
        file1 = await provider.save_file(
            self.create_mock_file("1.jpg", b"1"), subfolder=report_id
        )
        file2 = await provider.save_file(
            self.create_mock_file("2.jpg", b"2"), subfolder=report_id
        )

        report_dir = os.path.dirname(file1)

        await provider.delete_file(file1)

        assert not os.path.exists(file1)
        assert os.path.exists(file2)
        assert os.path.exists(report_dir)

    async def test_delete_non_existent_file_does_not_crash(self, provider):
        await provider.delete_file("/tmp/non_existent_path_123.jpg")
