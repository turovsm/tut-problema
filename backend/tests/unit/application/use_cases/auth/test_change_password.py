import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.auth import ChangePasswordDTO
from app.application.use_cases.auth.change_password import (
    ChangePasswordUseCase,
)
from app.domain.entities.user import User
from app.domain.exceptions.base import UnauthorizedException
from app.domain.exceptions.user import UserNotFoundException


class TestChangePasswordUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_auth_provider(self):
        provider = MagicMock()
        provider.verify_password.return_value = True
        provider.hash_password.return_value = "new_hashed_password"
        return provider

    @pytest.fixture
    def use_case(self, mock_user_repo, mock_auth_provider):
        return ChangePasswordUseCase(
            user_repo=mock_user_repo, auth_provider=mock_auth_provider
        )

    async def test_change_password_success(
        self, use_case, mock_user_repo, mock_auth_provider
    ):
        user_id = uuid.uuid4()
        user = User(
            id=user_id, email="t@t.com", username="u", password_hash="old_hash"
        )
        mock_user_repo.get_by_id.return_value = user

        dto = ChangePasswordDTO(
            user_id=user_id,
            current_password="OldPassword123!",
            new_password="NewSecurePassword456!",
        )

        await use_case.execute(dto)

        mock_auth_provider.verify_password.assert_called_once_with(
            "OldPassword123!", "old_hash"
        )
        mock_auth_provider.hash_password.assert_called_once_with(
            "NewSecurePassword456!"
        )
        assert user.password_hash == "new_hashed_password"
        mock_user_repo.save.assert_called_once_with(user)

    async def test_change_password_wrong_current(
        self, use_case, mock_user_repo, mock_auth_provider
    ):
        user = User(email="test@test.com", username="t", password_hash="h")
        mock_user_repo.get_by_id.return_value = user
        mock_auth_provider.verify_password.return_value = False

        dto = ChangePasswordDTO(
            user_id=uuid.uuid4(),
            current_password="WrongOldPassword",
            new_password="AnyNewPassword",
        )

        with pytest.raises(UnauthorizedException) as exc:
            await use_case.execute(dto)

        assert "Current password is incorrect" in exc.value.message
        mock_user_repo.save.assert_not_called()

    async def test_change_password_user_not_found(
        self, use_case, mock_user_repo
    ):
        mock_user_repo.get_by_id.return_value = None

        dto = ChangePasswordDTO(
            user_id=uuid.uuid4(), current_password="any", new_password="any"
        )

        with pytest.raises(UserNotFoundException):
            await use_case.execute(dto)
