import requests
from bs4 import BeautifulSoup
import time


class JDScraper:
    """
    Sadece ihtiyaç duyulduğunda JD detaylarını webden çeker.
    """

    def fetch_description(self, url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            print(f"🌍 JD İndiriliyor: {url}")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # AIESEC sayfasındaki metin genellikle belirli etiketlerdedir.
                # Sayfa yapısı dinamik olduğu için genelde tüm <p> etiketlerini toplamak güvenlidir.
                paragraphs = soup.find_all('p')
                full_text = " ".join([p.get_text() for p in paragraphs])

                # Metin çok uzunsa AI için kısalt (ilk 2000 karakter yeterli)
                return full_text[:2000] if full_text else "Detay bulunamadı."
            else:
                return f"Hata: Sayfa açılamadı (Kod: {response.status_code})"

        except Exception as e:
            return f"Bağlantı Hatası: {e}"

        finally:
            # Hızlı istek atıp engellenmemek için küçük bir bekleme
            time.sleep(1)