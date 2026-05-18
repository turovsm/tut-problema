import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.auth import AuthResultDTO, LoginDTO
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions.base import UnauthorizedException
from app.domain.exceptions.user import UserInactiveException


class TestLoginUserUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_auth_provider(self):
        provider = MagicMock()
        provider.verify_password.return_value = True
        provider.create_token.side_effect = ["access_jwt", "refresh_jwt"]
        return provider

    @pytest.fixture
    def use_case(self, mock_user_repo, mock_token_repo, mock_auth_provider):
        return LoginUserUseCase(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            auth_provider=mock_auth_provider,
            access_token_expiry_minutes=30,
            refresh_token_expiry_days=7,
        )

    async def test_login_success(
        self, use_case, mock_user_repo, mock_auth_provider, mock_token_repo
    ):
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="test@test.com",
            username="tester",
            password_hash="hashed",
            is_active=True,
        )
        mock_user_repo.get_by_email.return_value = user

        dto = LoginDTO(email="test@test.com", password="CorrectPassword123!")

        result = await use_case.execute(dto)

        assert isinstance(result, AuthResultDTO)
        assert result.user.id == user_id
        assert result.access_token == "access_jwt"
        assert result.refresh_token == "refresh_jwt"
        assert result.access_max_age == 30 * 60
        assert result.refresh_max_age == 7 * 24 * 60 * 60

        mock_token_repo.save_refresh_token.assert_called_once()

        mock_auth_provider.create_token.assert_any_call(
            payload={"sub": str(user_id), "type": "access"},
            expires_delta_minutes=30,
        )

    async def test_login_invalid_credentials(
        self, use_case, mock_user_repo, mock_auth_provider
    ):
        user = User(email="test@test.com", username="t", password_hash="h")
        mock_user_repo.get_by_email.return_value = user
        mock_auth_provider.verify_password.return_value = False

        dto = LoginDTO(email="test@test.com", password="WrongPassword")

        with pytest.raises(UnauthorizedException):
            await use_case.execute(dto)

    async def test_login_user_not_found(self, use_case, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None

        dto = LoginDTO(email="ghost@test.com", password="any")

        with pytest.raises(UnauthorizedException):
            await use_case.execute(dto)

    async def test_login_inactive_user(self, use_case, mock_user_repo):
        user = User(
            id=uuid.uuid4(),
            email="blocked@test.com",
            username="blocked",
            password_hash="hashed_val",
            is_active=False,
        )
        mock_user_repo.get_by_email.return_value = user

        dto = LoginDTO(email="blocked@test.com", password="any")

        with pytest.raises(UserInactiveException):
            await use_case.execute(dto)
