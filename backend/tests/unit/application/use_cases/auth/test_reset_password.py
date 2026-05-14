import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.auth import ResetPasswordDTO
from app.application.use_cases.auth.reset_password import ResetPasswordUseCase
from app.domain.entities.token import VerificationToken
from app.domain.entities.user import User
from app.domain.exceptions.base import BusinessRuleException
from app.domain.exceptions.user import UserNotFoundException


class TestResetPasswordUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_auth_provider(self):
        provider = MagicMock()
        provider.hash_password.return_value = "new_hashed_password"
        return provider

    @pytest.fixture
    def use_case(self, mock_user_repo, mock_token_repo, mock_auth_provider):
        return ResetPasswordUseCase(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            auth_provider=mock_auth_provider,
        )

    async def test_reset_password_success(
        self, use_case, mock_user_repo, mock_token_repo, mock_auth_provider
    ):
        user_id = uuid.uuid4()
        token_uuid = uuid.uuid4()

        token_entity = VerificationToken(
            user_id=user_id,
            token=token_uuid,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        mock_token_repo.get_verification_token.return_value = token_entity

        user = User(
            id=user_id, email="t@t.com", username="u", password_hash="old_h"
        )
        mock_user_repo.get_by_id.return_value = user

        dto = ResetPasswordDTO(
            token=token_uuid, new_password="NewSecretPassword123!"
        )

        await use_case.execute(dto)

        mock_auth_provider.hash_password.assert_called_once_with(
            "NewSecretPassword123!"
        )
        assert user.password_hash == "new_hashed_password"

        mock_user_repo.save.assert_called_once_with(user)
        mock_token_repo.delete_verification_token.assert_called_once_with(
            token_uuid
        )

    async def test_reset_password_token_not_found(
        self, use_case, mock_token_repo
    ):
        mock_token_repo.get_verification_token.return_value = None

        with pytest.raises(BusinessRuleException) as exc:
            await use_case.execute(
                ResetPasswordDTO(token=uuid.uuid4(), new_password="any")
            )
        assert "Invalid or expired" in exc.value.message

    async def test_reset_password_token_expired(
        self, use_case, mock_token_repo
    ):
        token_uuid = uuid.uuid4()
        expired_token = VerificationToken(
            user_id=uuid.uuid4(),
            token=token_uuid,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        mock_token_repo.get_verification_token.return_value = expired_token

        with pytest.raises(BusinessRuleException):
            await use_case.execute(
                ResetPasswordDTO(token=token_uuid, new_password="any")
            )

        mock_token_repo.delete_verification_token.assert_called_once_with(
            token_uuid
        )

    async def test_reset_password_user_not_found(
        self, use_case, mock_user_repo, mock_token_repo
    ):
        token_entity = VerificationToken(
            user_id=uuid.uuid4(),
            token=uuid.uuid4(),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        mock_token_repo.get_verification_token.return_value = token_entity
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            await use_case.execute(
                ResetPasswordDTO(token=token_entity.token, new_password="any")
            )
