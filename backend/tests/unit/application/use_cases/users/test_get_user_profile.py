import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.users.get_user_profile import (
    GetUserProfileUseCase,
)
from app.domain.entities.user import User
from app.domain.exceptions.user import UserNotFoundException


class TestGetUserProfileUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_user_repo):
        return GetUserProfileUseCase(user_repo=mock_user_repo)

    async def test_get_profile_success(self, use_case, mock_user_repo):
        user_id = uuid.uuid4()
        expected_user = User(
            id=user_id,
            email="profile@test.com",
            username="profile_owner",
            password_hash="hashed_pw",
        )
        mock_user_repo.get_by_id.return_value = expected_user

        result = await use_case.execute(user_id)

        assert result == expected_user
        assert result.username == "profile_owner"
        mock_user_repo.get_by_id.assert_called_once_with(user_id)

    async def test_get_profile_not_found(self, use_case, mock_user_repo):
        user_id = uuid.uuid4()
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundException):
            await use_case.execute(user_id)

        mock_user_repo.get_by_id.assert_called_once_with(user_id)
