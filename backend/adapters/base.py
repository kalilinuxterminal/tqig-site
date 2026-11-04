from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Callable

class DeviceConnectionAdapter(ABC):
    id: str
    @abstractmethod
    async def discover(self) -> list[dict]: ...
    @abstractmethod
    def open(self, device_id: str) -> AbstractAsyncContextManager: ...
    @abstractmethod
    def capabilities(self) -> dict: ...

class UnavailableTransport(RuntimeError):
    pass
