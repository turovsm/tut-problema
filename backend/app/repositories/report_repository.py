from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.report import Report, ReportPhoto
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: AsyncSession):
        super().__init__(Report, db)

    async def get_with_relations(self, report_id: UUID) -> Optional[Report]:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.created_by),
                selectinload(self.model.photos),
            )
            .where(self.model.id == report_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_photo(self, photo: ReportPhoto):
        self.db.add(photo)
        await self.db.flush()
