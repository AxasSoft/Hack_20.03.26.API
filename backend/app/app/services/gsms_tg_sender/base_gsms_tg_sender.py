from abc import ABC, abstractmethod
from typing import Optional


class BaseTgSender(ABC):
    @abstractmethod
    async def send(self, tel: str, code: Optional[str] = None) -> str:
        pass
