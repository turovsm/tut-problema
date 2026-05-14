import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.auth import RefreshTokenDTO
from app.application.use_cases.auth.logout_user import LogoutUserUseCase
from app.domain.entities.token import RefreshToken


class TestLogoutUserUseCase:
    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_auth_provider(self):
        provider = MagicMock()
        provider.decode_token.return_value = {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "jti": "valid_jti",
        }
        return provider

    @pytest.fixture
    def use_case(self, mock_token_repo, mock_auth_provider):
        return LogoutUserUseCase(
            token_repo=mock_token_repo, auth_provider=mock_auth_provider
        )

    async def test_logout_success(
        self, use_case, mock_token_repo, mock_auth_provider
    ):
        user_id = uuid.uuid4()
        jti = "valid_jti"

        stored_token = RefreshToken(
            jti=jti,
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked_at=None,
        )
        mock_token_repo.get_refresh_token.return_value = stored_token

        await use_case.execute(RefreshTokenDTO(refresh_token="jwt_string"))

        assert stored_token.revoked_at is not None
        mock_token_repo.save_refresh_token.assert_called_once_with(
            stored_token
        )

    async def test_logout_invalid_jwt(
        self, use_case, mock_auth_provider, mock_token_repo
    ):
        mock_auth_provider.decode_token.return_value = None

        await use_case.execute(RefreshTokenDTO(refresh_token="fake_jwt"))

        mock_token_repo.get_refresh_token.assert_not_called()
        mock_token_repo.save_refresh_token.assert_not_called()

    async def test_logout_wrong_token_type(
        self, use_case, mock_auth_provider, mock_token_repo
    ):
        mock_auth_provider.decode_token.return_value = {"type": "access"}

        await use_case.execute(RefreshTokenDTO(refresh_token="access_jwt"))

        mock_token_repo.get_refresh_token.assert_not_called()

    async def test_logout_token_not_found_in_db(
        self, use_case, mock_token_repo
    ):
        mock_token_repo.get_refresh_token.return_value = None

        await use_case.execute(
            RefreshTokenDTO(refresh_token="valid_jwt_but_missing_in_db")
        )

        mock_token_repo.save_refresh_token.assert_not_called()

    async def test_logout_already_revoked(self, use_case, mock_token_repo):
        already_revoked = RefreshToken(
            jti="j",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(UTC),
            revoked_at=datetime.now(UTC),
        )
        mock_token_repo.get_refresh_token.return_value = already_revoked

        await use_case.execute(RefreshTokenDTO(refresh_token="jwt"))

        mock_token_repo.save_refresh_token.assert_not_called()
