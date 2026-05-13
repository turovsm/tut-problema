import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.auth import ForgotPasswordDTO
from app.application.use_cases.auth.forgot_password import (
    ForgotPasswordUseCase,
)
from app.domain.entities.user import User


class TestForgotPasswordUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_email_provider(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_user_repo, mock_token_repo, mock_email_provider):
        return ForgotPasswordUseCase(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            email_provider=mock_email_provider,
            reset_token_expiry_hours=1,
        )

    async def test_forgot_password_success(
        self, use_case, mock_user_repo, mock_token_repo, mock_email_provider
    ):
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="registered@test.com",
            username="tester",
            password_hash="h",
        )
        mock_user_repo.get_by_email.return_value = user

        dto = ForgotPasswordDTO(email="registered@test.com")

        await use_case.execute(dto)

        mock_token_repo.delete_verification_tokens_by_user.assert_called_once_with(
            user_id
        )
        mock_token_repo.save_verification_token.assert_called_once()
        mock_email_provider.send_password_reset.assert_called_once()

    async def test_forgot_password_silent_fail(
        self, use_case, mock_user_repo, mock_token_repo, mock_email_provider
    ):
        mock_user_repo.get_by_email.return_value = None

        dto = ForgotPasswordDTO(email="unknown@test.com")

        await use_case.execute(dto)

        mock_token_repo.save_verification_token.assert_not_called()
        mock_email_provider.send_password_reset.assert_not_called()
