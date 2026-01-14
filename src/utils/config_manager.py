import os
from dotenv import load_dotenv


class ConfigManager:
    """
    Singleton Pattern: Uygulama ayarlarını güvenli bir şekilde merkezi olarak yönetir.
    """

    def __init__(self):
        load_dotenv()  # .env dosyasındaki verileri yükler

    def get_api_key(self, key_name: str):
        value = os.getenv(key_name)
        if not value:
            raise ValueError(f"Kritik Güvenlik Hatası: {key_name} .env dosyasında bulunamadı!")
        return value


# Kullanımı için bir örnek nesne
config = ConfigManager()