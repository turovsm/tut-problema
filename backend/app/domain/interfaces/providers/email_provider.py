from abc import ABC, abstractmethod


class IEmailProvider(ABC):
    @abstractmethod
    async def send_verification(
        self, email: str, name: str, token: str
    ) -> bool: ...

    @abstractmethod
    async def send_password_reset(
        self, email: str, name: str, token: str
    ) -> bool: ...
