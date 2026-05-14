import uuid
from unittest.mock import AsyncMock

import pytest

from app.application.dto.users import ListUsersDTO
from app.application.use_cases.users.list_all_users import ListAllUsersUseCase
from app.domain.entities.enums import UserRole
from app.domain.entities.user import User
from app.domain.exceptions.base import PermissionDeniedException


class TestListAllUsersUseCase:
    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_user_repo):
        return ListAllUsersUseCase(user_repo=mock_user_repo)

    @pytest.fixture
    def sample_users(self):
        return [
            User(
                id=uuid.uuid4(),
                email="1@t.com",
                username="u1",
                password_hash="h",
            ),
            User(
                id=uuid.uuid4(),
                email="2@t.com",
                username="u2",
                password_hash="h",
            ),
        ], 2

    async def test_list_users_success_as_moderator(
        self, use_case, mock_user_repo, sample_users
    ):
        users_list, total_count = sample_users
        mock_user_repo.get_all.return_value = (users_list, total_count)

        dto = ListUsersDTO(user_role=UserRole.MODERATOR, page=2, limit=5)

        items, total = await use_case.execute(dto)

        mock_user_repo.get_all.assert_called_once_with(limit=5, offset=5)

        assert total == 2
        assert len(items) == 2
        assert items[0].username == "u1"

    async def test_list_users_success_as_gov_org(
        self, use_case, mock_user_repo, sample_users
    ):
        mock_user_repo.get_all.return_value = sample_users

        dto = ListUsersDTO(user_role=UserRole.GOV_ORG, page=1, limit=20)
        await use_case.execute(dto)

        mock_user_repo.get_all.assert_called_once()

    async def test_list_users_forbidden_for_regular_user(
        self, use_case, mock_user_repo
    ):
        dto = ListUsersDTO(user_role=UserRole.USER, page=1, limit=20)

        with pytest.raises(PermissionDeniedException):
            await use_case.execute(dto)

        mock_user_repo.get_all.assert_not_called()
