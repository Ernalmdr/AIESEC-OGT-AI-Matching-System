import time
import sys
import os
import json

# Yolları Tanıt
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.repositories.podio_repo import PodioRepository
from src.repositories.expa_repo import ExpaRepository
from src.repositories.google_sheets_repo import GoogleSheetsRepository
from src.services.ai_matcher import AIMatcher
from src.services.jd_scraper import JDScraper

# --- AYARLAR ---
APP_ID = "23409870"  # Senin istediğin yeni ID
VIEW_ID = 61478954  # "Sign Up" listesinin View ID'si (Örn: "567890"). Boş bırakırsan hepsini çeker.
HISTORY_FILE = "processed_history.json"  # Hafıza dosyası


def load_history():
    """Daha önce işlem yapılan kişilerin ID listesini yükler."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()


def save_history(processed_ids):
    """İşlem yapılan kişileri dosyaya kaydeder."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(processed_ids), f)


def run_bot():
    print("🤖OGT AI Bot v2.1 (Ha fızalı Mod) Başlatılıyor...")

    # 0. Hafızayı Yükle
    processed_ids = load_history()
    print(f"🧠 Hafıza yüklendi: {len(processed_ids)} kişi daha önce işlenmiş.")

    # 1. Servisleri Başlat
    try:
        podio = PodioRepository()
        expa = ExpaRepository()
        ai = AIMatcher()
        scraper = JDScraper()
        sheets = GoogleSheetsRepository()
        print("✅ Servisler hazır.")
    except Exception as e:
        print(f"❌ Başlatma Hatası: {e}")
        return

    # 2. EXPA'dan Projeleri Çek
    print("🌍 EXPA Projeleri taranıyor...")
    all_projects = expa.fetch_data()
    print(f"✅ {len(all_projects)} aktif proje bulundu.")

    # 3. Podio'dan Adayları Çek
    try:
        # View ID varsa onu kullanır, yoksa App ID'deki herkesi çeker
        applicants = podio.fetch_applicants(APP_ID, view_id=VIEW_ID)
        print(f"👥 Podio'dan {len(applicants)} aday çekildi.")
    except Exception as e:
        print(f"❌ Podio Erişim Hatası: {e}")
        return

    # 4. Döngü
    new_processed_count = 0

    for i, ep in enumerate(applicants):
        # --- TEKRAR KONTROLÜ ---
        if ep.ep_id in processed_ids:
            print(f"⏭️  ATLANIYOR: {ep.full_name} (Daha önce işlendi)")
            continue

        print(f"\n[{i + 1}/{len(applicants)}] İşleniyor: {ep.full_name}")

        # --- A. Basit Filtreleme ---
        scored_projects = []
        keywords = (ep.background + " " + " ".join(ep.skills)).lower().split()

        for p in all_projects:
            score = 0
            p_text = (p.title + " " + p.organisation).lower()
            for k in keywords:
                if len(k) > 3 and k in p_text: score += 10
            if score > 0: scored_projects.append((score, p))

        scored_projects.sort(key=lambda x: x[0], reverse=True)
        top_match = scored_projects[0][1] if scored_projects else None

        if top_match:
            print(f"   🔍 Eşleşme: {top_match.title} ({top_match.country})")

            # --- B. Web Scraping ---
            if top_match.link:
                try:
                    desc = scraper.fetch_description(top_match.link)
                    top_match.description = desc
                except:
                    pass

            # --- C. AI Analizi ---
            print("   🧠 AI Analiz Yapıyor...")
            results = ai.generate_batch_report(ep, [top_match], cv_content="")

            if results:
                res = results[0]

                # --- D. Sheet'e Yaz (Sessiz Mod) ---
                sheets.log_match(
                    "OGT_Analiz_Loglari",
                    ep.full_name, top_match.title, top_match.organisation, top_match.country,
                    res.get('score'), res.get('sales_pitch')
                )
                print("   📊 Tabloya işlendi.")

                # --- E. BAŞARILI OLUNCA HAFIZAYA EKLE ---
                processed_ids.add(ep.ep_id)
                save_history(processed_ids)  # Her başarılı işlemde kaydet
                new_processed_count += 1
            else:
                print("   ⚠️ AI sonuç döndüremedi.")
        else:
            print("   🚫 Uygun proje bulunamadı.")

        time.sleep(1)

    print(f"\n🏁 Tamamlandı! {new_processed_count} yeni kişi işlendi.")


if __name__ == "__main__":
    run_bot()