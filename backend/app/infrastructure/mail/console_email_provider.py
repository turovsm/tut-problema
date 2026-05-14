from app.core.config import settings
from app.domain.interfaces.providers.email_provider import IEmailProvider


class ConsoleEmailProvider(IEmailProvider):
    def __init__(self):
        self.frontend_url = settings.FRONTEND_URL

    async def send_verification(
        self, email: str, name: str, token: str
    ) -> bool:
        verification_url = (
            f"{self.frontend_url}/auth/verify-email?token={token}"
        )

        print("\n" + "=" * 50)
        print("[CONSOLE EMAIL] ПОДТВЕРЖДЕНИЕ EMAIL")
        print(f"Кому: {name} <{email}>")
        print("Тема: Подтверждение регистрации на ТутПроблема")
        print(f"Ссылка: {verification_url}")
        print("=" * 50 + "\n")

        return True

    async def send_password_reset(
        self, email: str, name: str, token: str
    ) -> bool:
        reset_url = f"{self.frontend_url}/auth/reset-password?token={token}"

        print("\n" + "=" * 50)
        print("[CONSOLE EMAIL] СБРОС ПАРОЛЯ")
        print(f"Кому: {name} <{email}>")
        print("Тема: Запрос на восстановление пароля")
        print(f"Ссылка: {reset_url}")
        print("=" * 50 + "\n")

        return True
