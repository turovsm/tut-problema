from abc import ABC, abstractmethod


class IAuthProvider(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str: ...

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool: ...

    @abstractmethod
    def create_token(
        self, payload: dict, expires_delta_minutes: int
    ) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> dict | None: ...
