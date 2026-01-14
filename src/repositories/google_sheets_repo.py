import gspread
import os
from google.oauth2.service_account import Credentials
from src.interfaces.data_provider import IDataProvider
from src.core.models import OGTProject


class GoogleSheetsRepository(IDataProvider):
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id

        # Dosya yolunu bulma (Güvenlik)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        creds_file = os.path.join(project_root, "credentials.json")

        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        try:
            creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        except Exception as e:
            raise Exception(f"Bağlantı Hatası: {e}")

    def fetch_data(self, program_type: str = "GTa") -> list[OGTProject]:
        sheet_map = {
            "GTa": "Opportunities Tracker | GTa",
            "GTe": "Opportunities Tracker | GTe"
        }

        target_sheet_name = sheet_map.get(program_type)
        if not target_sheet_name:
            raise ValueError("Geçersiz program türü!")

        print(f"🔄 '{target_sheet_name}' sekmesinden veriler çekiliyor...")

        try:
            worksheet = self.spreadsheet.worksheet(target_sheet_name)
        except gspread.WorksheetNotFound:
            print(f"❌ HATA: '{target_sheet_name}' sekmesi bulunamadı!")
            return []

        all_rows = worksheet.get_all_values()

        # Başlık satırını belirle (4. indeks = 5. satır)
        HEADER_ROW_INDEX = 4
        if len(all_rows) <= HEADER_ROW_INDEX: return []

        headers = all_rows[HEADER_ROW_INDEX]
        data_rows = all_rows[HEADER_ROW_INDEX + 1:]

        # Sütun indekslerini isme göre bul
        def get_col_idx(keywords):
            for i, h in enumerate(headers):
                if any(k in str(h).lower() for k in keywords):
                    return i
            return -1

        # Kritik sütunları bul
        idx_id = get_col_idx(["op id", "id"])
        idx_field = get_col_idx(["field", "title"])
        idx_company = get_col_idx(["company"])
        idx_mc = get_col_idx(["mc", "entity", "country"])
        idx_salary = get_col_idx(["salary"])
        idx_duration = get_col_idx(["duration"])
        idx_status = get_col_idx(["status"])  # Artık sadece bilgi amaçlı çekiyoruz

        print(f"📊 {len(data_rows)} satır işleniyor (Filtre kapalı)...")

        projects = []
        for row in data_rows:
            if not row: continue

            # Güvenli Veri Okuma
            def get_val(idx):
                return row[idx] if idx != -1 and len(row) > idx else ""

            # --- ARTIK FİLTRE YOK ---
            # Statü ne olursa olsun (tarih, open, boş) projeyi alıyoruz.

            op_id = str(get_val(idx_id))

            # Eğer ID yoksa boş satırdır, atla
            if not op_id or op_id == "":
                continue

            full_link = f"https://aiesec.org/opportunity/global-talent/{op_id}"

            proj = OGTProject(
                op_id=op_id,
                title=str(get_val(idx_field)),
                company=str(get_val(idx_company)),
                country=str(get_val(idx_mc)),
                link=full_link,
                status=str(get_val(idx_status)),  # Bilgi olarak kalsın
                salary=str(get_val(idx_salary)),
                duration=str(get_val(idx_duration))
            )
            projects.append(proj)

        return projects
