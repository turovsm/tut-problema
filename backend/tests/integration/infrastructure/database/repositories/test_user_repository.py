import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.enums import UserRole
from app.domain.entities.user import User
from app.infrastructure.database.repositories.user_repository import (
    UserRepository,
)


class TestUserRepository:
    @pytest.fixture
    def repo(self, db_session: AsyncSession):
        return UserRepository(db_session)

    async def test_save_and_get_user(self, repo: UserRepository):
        new_user = User(
            email="test@example.com",
            username="test_user",
            password_hash="hashed_string",
            role=UserRole.USER,
        )

        saved_user = await repo.save(new_user)
        assert saved_user.id == new_user.id

        found_user = await repo.get_by_id(new_user.id)

        assert found_user is not None
        assert found_user.email == "test@example.com"
        assert found_user.username == "test_user"

    async def test_get_by_email_exists(self, repo: UserRepository):
        email = "unique@test.com"
        user = User(email=email, username="u1", password_hash="h")
        await repo.save(user)

        found = await repo.get_by_email(email)
        assert found is not None
        assert found.id == user.id

    async def test_get_by_username_exists(self, repo: UserRepository):
        username = "unique_bob"
        user = User(email="bob@test.com", username=username, password_hash="h")
        await repo.save(user)

        found = await repo.get_by_username(username)
        assert found is not None
        assert found.email == "bob@test.com"

    async def test_get_all_paginated(self, repo: UserRepository):
        for i in range(3):
            await repo.save(
                User(email=f"{i}@t.com", username=f"u{i}", password_hash="h")
            )

        users, total = await repo.get_all(limit=2, offset=0)

        assert total == 3
        assert len(users) == 2

    async def test_update_existing_user(self, repo: UserRepository):
        user = User(email="old@t.com", username="old_name", password_hash="h")
        await repo.save(user)

        user.username = "new_name"
        await repo.save(user)

        updated = await repo.get_by_id(user.id)
        assert updated.username == "new_name"
