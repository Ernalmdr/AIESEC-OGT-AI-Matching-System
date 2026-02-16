from abc import ABC, abstractmethod

class IDataProvider(ABC):
    @abstractmethod
    async def fetch_data_async(self, programme_id: int = 8):
        pass