from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.interfaces.repositories.user_repository import IUserRepository
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.repositories.base import (
    BaseSQLAlchemyRepository,
)


class UserRepository(BaseSQLAlchemyRepository[UserModel], IUserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(UserModel, session)

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            password_hash=model.password_hash,
            role=model.role,
            is_active=model.is_active,
            is_verified=model.is_verified,
            created_at=model.created_at,
        )

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._get_by_id(user_id)
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        query = select(self._model).where(self._model.email == email)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        query = select(self._model).where(self._model.username == username)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_all(self, limit: int = 20, offset: int = 0) -> list[User]:
        count_query = select(func.count()).select_from(self._model)
        total = await self._session.execute(count_query)

        query = (
            select(self._model)
            .order_by(self._model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(query)

        return [self._to_domain(m) for m in result.scalars().all()], (
            total.scalar() or 0
        )

    async def save(self, user: User) -> User:
        model = await self._get_by_id(user.id)

        if not model:
            model = UserModel(
                id=user.id,
                email=user.email,
                username=user.username,
                password_hash=user.password_hash,
                role=user.role,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
            )
        else:
            model.email = user.email
            model.username = user.username
            model.password_hash = user.password_hash
            model.role = user.role
            model.is_active = user.is_active
            model.is_verified = user.is_verified

        model = await self._save(model)
        return self._to_domain(model)
