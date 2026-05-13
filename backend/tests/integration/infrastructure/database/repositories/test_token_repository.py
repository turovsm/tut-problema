import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.token import RefreshToken, VerificationToken
from app.domain.entities.user import User
from app.infrastructure.database.repositories.token_repository import (
    TokenRepository,
)
from app.infrastructure.database.repositories.user_repository import (
    UserRepository,
)


class TestTokenRepository:
    @pytest.fixture
    async def sample_user(self, db_session: AsyncSession):
        """Создает пользователя для привязки токенов."""
        user_repo = UserRepository(db_session)
        user = User(
            email="token_test@test.com",
            username="token_user",
            password_hash="h",
        )
        return await user_repo.save(user)

    @pytest.fixture
    def repo(self, db_session: AsyncSession):
        return TokenRepository(db_session)

    async def test_refresh_token_lifecycle(
        self, repo: TokenRepository, sample_user: User
    ):
        jti = "test_jti_123"
        expires = datetime.now(UTC) + timedelta(days=7)

        token_entity = RefreshToken(
            jti=jti,
            user_id=sample_user.id,
            expires_at=expires,
            revoked_at=None,
        )

        await repo.save_refresh_token(token_entity)

        found = await repo.get_refresh_token(jti)
        assert found is not None
        assert found.user_id == sample_user.id
        assert found.revoked_at is None

        revoked_time = datetime.now(UTC)
        token_entity.revoked_at = revoked_time
        await repo.save_refresh_token(token_entity)

        updated = await repo.get_refresh_token(jti)
        assert updated.revoked_at is not None
        assert updated.revoked_at.year == revoked_time.year

    async def test_verification_token_lifecycle(
        self, repo: TokenRepository, sample_user: User
    ):
        token_uuid = uuid.uuid4()
        expires = datetime.now(UTC) + timedelta(hours=1)

        token_entity = VerificationToken(
            user_id=sample_user.id, token=token_uuid, expires_at=expires
        )

        await repo.save_verification_token(token_entity)

        found = await repo.get_verification_token(token_uuid)
        assert found is not None
        assert found.user_id == sample_user.id

        await repo.delete_verification_token(token_uuid)

        assert await repo.get_verification_token(token_uuid) is None

    async def test_delete_all_verification_tokens_for_user(
        self, repo: TokenRepository, sample_user: User
    ):
        uids = [uuid.uuid4(), uuid.uuid4()]
        for uid in uids:
            t = VerificationToken(
                user_id=sample_user.id,
                token=uid,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
            await repo.save_verification_token(t)

        await repo.delete_verification_tokens_by_user(sample_user.id)

        assert await repo.get_verification_token(uids[0]) is None
        assert await repo.get_verification_token(uids[1]) is None

    async def test_delete_verification_tokens_does_not_affect_others(
        self,
        repo: TokenRepository,
        sample_user: User,
        db_session: AsyncSession,
    ):
        user_repo = UserRepository(db_session)
        other_user = await user_repo.save(
            User(email="2@t.com", username="u2", password_hash="h")
        )

        token_me = uuid.uuid4()
        token_other = uuid.uuid4()

        await repo.save_verification_token(
            VerificationToken(
                user_id=sample_user.id,
                token=token_me,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        await repo.save_verification_token(
            VerificationToken(
                user_id=other_user.id,
                token=token_other,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )

        await repo.delete_verification_tokens_by_user(sample_user.id)

        assert await repo.get_verification_token(token_me) is None
        assert await repo.get_verification_token(token_other) is not None
