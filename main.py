import sys
import os
from dotenv import load_dotenv

# --- 🛠️ YOL DÜZELTME (PATH FIX) ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- 📦 IMPORTLAR ---

try:
    from src.repositories.expa_repo import ExpaRepository
    from src.services.ai_matcher import AIMatcher
    from src.core.models import ExchangeParticipant
except ImportError as e:
    print(f"❌ Import Hatası: {e}")
    print("İpucu: 'src' klasörünün içinde __init__.py dosyaları olduğundan emin ol.")
    sys.exit(1)

# .env dosyasındaki GEMINI_API_KEY ve EXPA_ACCESS_TOKEN'ı yükler.
load_dotenv()


def run_system():
    try:
        # 1. Servisleri Başlat
        expa = ExpaRepository()
        matcher = AIMatcher()

        # 2. Test Adayı (Sıla Top)
        test_ep = ExchangeParticipant(
            ep_id="5946835",
            full_name="Sıla Top",
            email="sila.top@aiesec.net",
            background="Marketing and Business Administration",
            skills=["Digital Marketing", "Social Media", "English"]
        )

        print(f"🚀 {test_ep.full_name} için eşleştirme sistemi başlatıldı...")

        # 3. EXPA'dan Verileri Çek (GTa programı id=8)
        print("🔄 EXPA API'den güncel projeler çekiliyor...")
        projects = expa.fetch_data(programme_id=8)

        if projects:
            print(f"✅ {len(projects)} proje başarıyla çekildi. Gemini AI analizi başlıyor...\n")

            # İlk 3 projeyi test amaçlı analiz edelim
            for p in projects[:3]:
                print(f"🧐 Analiz Ediliyor: {p.title} ({p.organisation})")

                # Gemini üzerinden rapor oluştur
                report = matcher.generate_match_report(test_ep, p)

                print("\n" + "=" * 60)
                print(f"📊 EŞLEŞME ANALİZİ: {p.title}")
                print("=" * 60)
                print(report)
                print("=" * 60 + "\n")
        else:
            print("❌ EXPA'dan veri çekilemedi. Token süresini veya internet bağlantısını kontrol et.")

    except Exception as e:
        print(f"⚠️ Kritik Bir Hata Oluştu: {e}")


if __name__ == "__main__":
    run_system()