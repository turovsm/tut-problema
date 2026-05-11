from app.domain.entities.enums import UserRole
from app.domain.entities.user import User
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.interfaces.repositories.user_repository import IUserRepository


class ListAllUsersUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_role: str) -> list[User]:
        # 1. Проверка прав доступа
        if user_role not in [UserRole.MODERATOR, UserRole.GOV_ORG]:
            raise PermissionDeniedException(
                "Insufficient permissions to view all users"
            )

        # 2. Получение данных из репозитория
        users = await self.user_repo.get_all()

        return users
