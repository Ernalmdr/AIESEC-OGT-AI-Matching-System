import os
import sys
from dotenv import load_dotenv

# Proje kök dizinini Python yoluna ekle (Import hatası almamak için)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.repositories.google_sheets_repo import GoogleSheetsRepository

load_dotenv()


def test_fetch_gta():
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    repo = GoogleSheetsRepository(sheet_id)

    # GTa sekmesini test et
    projects = repo.fetch_data(program_type="GTa")

    if projects:
        print("\n✅ İlk Proje Örneği:")
        print(projects[0])
    else:
        print("⚠️ Hiç proje bulunamadı veya Status='open' olan yok.")


if __name__ == "__main__":
    test_fetch_gta()