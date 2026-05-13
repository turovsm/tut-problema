import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.auth import AuthResultDTO, RefreshTokenDTO
from app.application.use_cases.auth.refresh_token import RefreshTokenUseCase
from app.domain.entities.token import RefreshToken
from app.domain.entities.user import User
from app.domain.exceptions.base import UnauthorizedException
from app.domain.exceptions.user import UserInactiveException


class TestRefreshTokenUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_auth_provider(self):
        provider = MagicMock()
        provider.decode_token.return_value = {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "jti": "old_jti",
        }
        provider.create_token.side_effect = [
            "new_access_jwt",
            "new_refresh_jwt",
        ]
        return provider

    @pytest.fixture
    def use_case(self, mock_user_repo, mock_token_repo, mock_auth_provider):
        return RefreshTokenUseCase(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            auth_provider=mock_auth_provider,
            access_token_expiry_minutes=30,
            refresh_token_expiry_days=7,
        )

    async def test_refresh_success(
        self, use_case, mock_user_repo, mock_token_repo, mock_auth_provider
    ):
        user_id = uuid.uuid4()
        old_jti = "old_jti"

        mock_auth_provider.decode_token.return_value = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": old_jti,
        }

        stored_token = RefreshToken(
            jti=old_jti,
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked_at=None,
        )
        mock_token_repo.get_refresh_token.return_value = stored_token

        user = User(
            id=user_id,
            email="t@t.com",
            username="u",
            password_hash="h",
            is_active=True,
        )
        mock_user_repo.get_by_id.return_value = user

        dto = RefreshTokenDTO(refresh_token="valid_old_jwt")

        result = await use_case.execute(dto)

        assert isinstance(result, AuthResultDTO)
        assert result.access_token == "new_access_jwt"
        assert result.refresh_token == "new_refresh_jwt"

        assert stored_token.revoked_at is not None
        mock_token_repo.save_refresh_token.assert_any_call(stored_token)

        assert mock_token_repo.save_refresh_token.call_count == 2

    async def test_refresh_token_revoked(self, use_case, mock_token_repo):
        stored_token = MagicMock(spec=RefreshToken)
        stored_token.revoked_at = datetime.now(UTC)
        mock_token_repo.get_refresh_token.return_value = stored_token

        with pytest.raises(UnauthorizedException) as exc:
            await use_case.execute(
                RefreshTokenDTO(refresh_token="revoked_jwt")
            )
        assert "revoked" in exc.value.message

    async def test_refresh_invalid_jwt(self, use_case, mock_auth_provider):
        mock_auth_provider.decode_token.return_value = None

        with pytest.raises(UnauthorizedException):
            await use_case.execute(RefreshTokenDTO(refresh_token="fake_jwt"))

    async def test_refresh_inactive_user(
        self, use_case, mock_user_repo, mock_token_repo
    ):
        mock_token_repo.get_refresh_token.return_value = RefreshToken(
            jti="j",
            user_id=uuid.uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )

        user = MagicMock(spec=User)
        user.is_active = False
        mock_user_repo.get_by_id.return_value = user

        with pytest.raises(UserInactiveException):
            await use_case.execute(RefreshTokenDTO(refresh_token="valid_jwt"))
