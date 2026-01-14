import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()


def test_google_sheets_connection():
    print("--- Google Sheets Bağlantı Testi Başlatıldı ---")

    # 1. Adım: Kimlik bilgilerini ve ID'yi .env'den al (SOLID: Config Management)
    # Bu dosyanın (test_sheets_conn.py) nerede olduğunu bul
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Bir üst klasöre (Proje Ana Dizinine) çık
    project_root = os.path.dirname(current_dir)

    # Ana dizindeki credentials.json yolunu oluştur
    creds_file = os.path.join(project_root, "credentials.json")
    sheet_id = os.getenv("1VYVGgIAo2WTllPz35ogucZCFYmvoZSvp8QRzmEhR-rg")

    if not sheet_id:
        print("❌ HATA: 1VYVGgIAo2WTllPz35ogucZCFYmvoZSvp8QRzmEhR-rg .env dosyasında bulunamadı!")
        return

    # 2. Adım: Yetkilendirme Scope'larını tanımla
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        # 3. Adım: Bağlantıyı kur
        print(f"🔄 {creds_file} kullanılarak bağlanılıyor...")
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(creds)

        # 4. Adım: Dosyayı açmayı dene
        print(f"🔄 Sheet ID: {sheet_id} açılıyor...")
        sheet = client.open_by_key(sheet_id)

        # 5. Adım: İlk sayfanın adını oku
        worksheet = sheet.get_worksheet(0)
        print(f"✅ BAŞARILI! Bağlanılan Sayfa: {worksheet.title}")

    except FileNotFoundError:
        print(f"❌ HATA: '{creds_file}' dosyası bulunamadı. Lütfen ana dizine kopyalayın.")
    except gspread.exceptions.APIError as e:
        print(f"❌ GOOGLE API HATASI: {e}")
    except Exception as e:
        print(f"❌ BEKLENMEDİK HATA: {e}")


if __name__ == "__main__":
    test_google_sheets_connection()