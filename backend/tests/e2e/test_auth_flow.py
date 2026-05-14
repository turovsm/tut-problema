import re

import httpx
import pytest
from fastapi import status

from tests.conftest import wait_for_email


@pytest.mark.usefixtures("containers_infra")
class TestAuthFlowE2E:
    async def test_full_user_lifecycle(self, client: httpx.AsyncClient):
        email = "test@test.com"
        password = "SecurePassword123!"

        # 1. РЕГИСТРАЦИЯ
        register_payload = {
            "email": email,
            "username": "tester",
            "password": password,
        }
        await client.post("/api/auth/register", json=register_payload)

        # 2. ПОЛУЧЕНИЕ ТОКЕНА
        email_data = await wait_for_email(email_to=email)
        html_body = email_data["HTML"]

        token_match = re.search(r"token=([a-f0-9\-]{36})", html_body)
        assert token_match is not None, "Verification token not found in email"
        verification_token = token_match.group(1)

        # 3. ВЕРИФИКАЦИЯ
        await client.post(
            "/api/auth/verify-email", json={"token": verification_token}
        )

        # 4. ЛОГИН
        login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert login_resp.status_code == status.HTTP_200_OK
        assert login_resp.json()["data"]["is_verified"] is True
        assert "access_token" in client.cookies

        # 5. ИСПОЛЬЗОВАНИЕ API
        profile_resp = await client.get("/api/users/me")
        assert profile_resp.status_code == status.HTTP_200_OK
        assert profile_resp.json()["data"]["email"] == email

        # ВЫХОД
        logout_resp = await client.post("/api/auth/logout")
        assert logout_resp.status_code == status.HTTP_200_OK
        assert "access_token" not in client.cookies

    async def test_unauthorized_access_format(self, client: httpx.AsyncClient):
        client.cookies.clear()
        response = await client.get("/api/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["status"] == "error"
        assert data["code"] == 401
        assert "error" in data

    async def test_forbidden_access_unverified(
        self, client: httpx.AsyncClient
    ):
        email = "test@test.com"
        password = "SecurePassword123!"

        await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "username": "test",
                "password": password,
            },
        )
        await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

        response = await client.post("/api/reports", data={"title": "Test"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["status"] == "error"
        assert data["code"] == 403
        assert "Email not verified" in data["error"]
