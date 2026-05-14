import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.application.dto.auth import VerifyEmailDTO
from app.application.use_cases.auth.verify_email import VerifyEmailUseCase
from app.domain.entities.token import VerificationToken
from app.domain.entities.user import User
from app.domain.exceptions.base import BusinessRuleException
from app.domain.exceptions.user import UserNotFoundException


class TestVerifyEmailUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_user_repo, mock_token_repo):
        return VerifyEmailUseCase(
            user_repo=mock_user_repo, token_repo=mock_token_repo
        )

    async def test_verify_success(
        self, use_case, mock_user_repo, mock_token_repo
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
            id=user_id,
            email="t@t.com",
            username="u",
            password_hash="h",
            is_verified=False,
        )
        mock_user_repo.get_by_id.return_value = user

        await use_case.execute(VerifyEmailDTO(token=token_uuid))

        assert user.is_verified is True
        mock_user_repo.save.assert_called_once_with(user)
        mock_token_repo.delete_verification_token.assert_called_once_with(
            token_uuid
        )

    async def test_verify_token_not_found(self, use_case, mock_token_repo):
        mock_token_repo.get_verification_token.return_value = None

        with pytest.raises(BusinessRuleException) as exc:
            await use_case.execute(VerifyEmailDTO(token=uuid.uuid4()))
        assert "Invalid or expired" in exc.value.message

    async def test_verify_token_expired(self, use_case, mock_token_repo):
        token_uuid = uuid.uuid4()
        token_entity = VerificationToken(
            user_id=uuid.uuid4(),
            token=token_uuid,
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        mock_token_repo.get_verification_token.return_value = token_entity

        with pytest.raises(BusinessRuleException):
            await use_case.execute(VerifyEmailDTO(token=token_uuid))

        mock_token_repo.delete_verification_token.assert_called_once_with(
            token_uuid
        )

    async def test_verify_user_not_found(
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
            await use_case.execute(VerifyEmailDTO(token=token_entity.token))
