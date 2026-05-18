import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.auth import ResendVerificationDTO
from app.application.use_cases.auth.resend_verification import (
    ResendVerificationUseCase,
)
from app.domain.entities.user import User


class TestResendVerificationUseCase:
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
        return ResendVerificationUseCase(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            email_provider=mock_email_provider,
            verification_token_expiry_hours=24,
        )

    async def test_resend_success(
        self, use_case, mock_user_repo, mock_token_repo, mock_email_provider
    ):
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="not_verified@test.com",
            username="u",
            password_hash="h",
            is_verified=False,
        )
        mock_user_repo.get_by_email.return_value = user

        dto = ResendVerificationDTO(email="not_verified@test.com")

        await use_case.execute(dto)

        mock_token_repo.delete_verification_tokens_by_user.assert_called_once_with(
            user_id
        )
        mock_token_repo.save_verification_token.assert_called_once()
        mock_email_provider.send_verification.assert_called_once()

    async def test_resend_already_verified(
        self, use_case, mock_user_repo, mock_token_repo, mock_email_provider
    ):
        user = User(
            id=uuid.uuid4(),
            email="ok@test.com",
            username="u",
            password_hash="h",
            is_verified=True,
        )
        mock_user_repo.get_by_email.return_value = user

        await use_case.execute(ResendVerificationDTO(email="ok@test.com"))

        mock_token_repo.save_verification_token.assert_not_called()
        mock_email_provider.send_verification.assert_not_called()

    async def test_resend_user_not_found(
        self, use_case, mock_user_repo, mock_token_repo, mock_email_provider
    ):
        mock_user_repo.get_by_email.return_value = None

        await use_case.execute(ResendVerificationDTO(email="ghost@test.com"))

        mock_token_repo.save_verification_token.assert_not_called()
        mock_email_provider.send_verification.assert_not_called()
