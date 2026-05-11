from app.application.dto.auth import ChangePasswordDTO
from app.domain.exceptions.base import UnauthorizedException
from app.domain.exceptions.user import UserNotFoundException
from app.domain.interfaces.providers.auth_provider import IAuthProvider
from app.domain.interfaces.repositories.user_repository import IUserRepository


class ChangePasswordUseCase:
    def __init__(
        self, user_repo: IUserRepository, auth_provider: IAuthProvider
    ):
        self.user_repo = user_repo
        self.auth_provider = auth_provider

    async def execute(self, dto: ChangePasswordDTO) -> None:
        # 1. Получаем пользователя
        user = await self.user_repo.get_by_id(dto.user_id)

        if not user:
            raise UserNotFoundException()

        # 2. Проверяем, совпадает ли текущий пароль
        if not self.auth_provider.verify_password(
            dto.current_password, user.password_hash
        ):
            raise UnauthorizedException("Current password is incorrect")

        # 3. Хешируем новый пароль
        new_hash = self.auth_provider.hash_password(dto.new_password)

        # 4. Обновляем сущность и сохраняем
        user.password_hash = new_hash
        await self.user_repo.save(user)
