from typing import Any, Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseSQLAlchemyRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self._model = model
        self._session = session

    async def _get_by_id(self, id: UUID) -> ModelType | None:
        query = select(self._model).where(self._model.id == id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def _get_all(self) -> list[ModelType]:
        query = select(self._model)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def _save(self, orm_obj: ModelType) -> ModelType:
        self._session.add(orm_obj)
        await self._session.flush()
        return orm_obj

    async def _delete_by_id(self, id: UUID) -> bool:
        query = delete(self._model).where(self._model.id == id)
        result = await self._session.execute(query)
        return result.rowcount > 0

    async def _exists(self, **kwargs: Any) -> bool:
        query = select(self._model).filter_by(**kwargs)
        result = await self._session.execute(query)
        return result.scalar_one_or_none() is not None
