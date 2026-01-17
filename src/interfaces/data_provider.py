from abc import ABC, abstractmethod

class IDataProvider(ABC):
    @abstractmethod
    def fetch_data(self):
        """Tüm veri sağlayıcılar bu metodu uygulamak zorundadır."""
        pass