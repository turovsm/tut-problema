from abc import ABC, abstractmethod
from typing import Any


class IStorageProvider(ABC):
    @abstractmethod
    async def save_file(self, file: Any, subfolder: str) -> str: ...

    @abstractmethod
    async def delete_file(self, file_path: str) -> None: ...
