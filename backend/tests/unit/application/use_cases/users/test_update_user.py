import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.users import UpdateUserDTO
from app.application.use_cases.users.update_user import UpdateUserUseCase
from app.domain.entities.user import User
from app.domain.exceptions.user import (
    UsernameTakenException,
    UserNotFoundException,
)


class TestUpdateUserUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.save.side_effect = lambda x: x
        return repo

    @pytest.fixture
    def use_case(self, mock_user_repo):
        return UpdateUserUseCase(user_repo=mock_user_repo)

    @pytest.fixture
    def sample_user(self):
        return User(
            id=uuid.uuid4(),
            email="original@test.com",
            username="old_username",
            password_hash="hash",
        )

    async def test_update_username_success(
        self, use_case, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_by_username.return_value = None

        dto = UpdateUserDTO(user_id=sample_user.id, username="new_cool_name")

        result = await use_case.execute(dto)

        assert result.username == "new_cool_name"
        mock_user_repo.get_by_username.assert_called_once_with("new_cool_name")
        mock_user_repo.save.assert_called_once()

    async def test_update_username_taken(
        self, use_case, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_id.return_value = sample_user
        other_user = MagicMock(spec=User)
        other_user.id = uuid.uuid4()
        mock_user_repo.get_by_username.return_value = other_user

        dto = UpdateUserDTO(user_id=sample_user.id, username="busy_name")

        with pytest.raises(UsernameTakenException):
            await use_case.execute(dto)

        mock_user_repo.save.assert_not_called()

    async def test_update_same_username(
        self, use_case, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_by_username.return_value = sample_user

        dto = UpdateUserDTO(user_id=sample_user.id, username="old_username")

        result = await use_case.execute(dto)

        assert result.username == "old_username"

    async def test_update_user_not_found(self, use_case, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None

        dto = UpdateUserDTO(user_id=uuid.uuid4(), username="any")

        with pytest.raises(UserNotFoundException):
            await use_case.execute(dto)
