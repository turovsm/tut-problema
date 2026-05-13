import os

import httpx
import pytest

from app.infrastructure.mail.smtp_email_provider import SmtpEmailProvider


@pytest.mark.usefixtures("containers_infra")
class TestSmtpEmailProviderIntegration:
    @pytest.fixture
    def provider(self):
        return SmtpEmailProvider()

    @pytest.fixture
    def mailpit_api(self):
        return os.environ.get("MAILPIT_API_URL")

    async def _get_latest_message(self, api_url: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/messages")
            messages = response.json().get("messages", [])
            if not messages:
                return None

            msg_id = messages[0]["ID"]
            detail = await client.get(f"{api_url}/message/{msg_id}")
            return detail.json()

    async def test_send_verification_full_content(self, provider, mailpit_api):
        email = "verify@test.com"
        name = "test"
        token = "verify-123"

        success = await provider.send_verification(email, name, token)
        assert success is True

        msg = await self._get_latest_message(mailpit_api)
        assert msg is not None
        assert msg["From"]["Address"] == provider.user
        assert msg["To"][0]["Address"] == email
        assert "Подтверждение" in msg["Subject"]

        assert name in msg["HTML"]
        assert token in msg["HTML"]
        assert "auth/verify-email" in msg["HTML"]

        assert name in msg["Text"]
        assert token in msg["Text"]
        assert "auth/verify-email" in msg["Text"]

    async def test_send_password_reset_full_content(
        self, provider, mailpit_api
    ):
        email = "reset@test.com"
        name = "test"
        token = "reset-456"

        success = await provider.send_password_reset(email, name, token)
        assert success is True

        msg = await self._get_latest_message(mailpit_api)
        assert msg is not None
        assert msg["From"]["Address"] == provider.user
        assert msg["To"][0]["Address"] == email
        assert "Сброс пароля" in msg["Subject"]

        assert name in msg["HTML"]
        assert token in msg["HTML"]
        assert "/auth/reset-password" in msg["HTML"]

        assert name in msg["Text"]
        assert token in msg["Text"]
        assert "/auth/reset-password" in msg["Text"]

    async def test_send_email_error_handling(self, provider, monkeypatch):
        monkeypatch.setattr(provider, "port", 1)
        success = await provider.send_verification(
            "any@t.com", "User", "token"
        )
        assert success is False
