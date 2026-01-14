import requests
import os
from dotenv import load_dotenv
from src.interfaces.data_provider import IDataProvider
from src.core.models import OGTProject

load_dotenv()


class ExpaRepository(IDataProvider):
    def __init__(self):
        # .env dosyasındaki token'ı temizle ve al
        token = os.getenv("EXPA_ACCESS_TOKEN", "").strip()

        # Bearer eki yoksa ekle (AIESEC API standartı)
        if token and not token.startswith("Bearer "):
            token = f"Bearer {token}"

        self.url = "https://gis-api.aiesec.org/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": token
        }

    def fetch_data(self, programme_id: int = 8) -> list[OGTProject]:
        # Apps Script'teki token'ı .env'den al (Bearer kelimesini kaldırıyoruz)
        token = os.getenv("EXPA_ACCESS_TOKEN", "").replace("Bearer ", "").strip()

        # URL'ye token'ı parametre olarak ekliyoruz (Apps Script yöntemi)
        url_with_token = f"https://gis-api.aiesec.org/graphql?access_token={token}"

        # Apps Script'teki GraphQL sorgusunun aynısı (Sadece JD ekledik)
        query = """
        query AllOpportunity {
            allOpportunity(
                filters: {
                    programmes: 8,
                    statuses: ["open","live"]
                }
                pagination: { per_page: 50 }
            ) {
                data {
                    id
                    title
                    description
                    organisation { name }
                    home_mc { name }
                    home_lc { name }
                    specifics_info { salary salary_currency { alphabetic_code } }
                    backgrounds { constant_name }
                    opportunity_duration_type { duration_type }
                }
            }
        }
        """

        try:
            print(f"🔄 Apps Script yöntemiyle bağlanılıyor...")
            response = requests.post(
                url_with_token,
                json={'query': query},
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            print(f"📡 Yanıt Kodu: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ Hata: {response.text}")
                return []

            res_json = response.json()
            # ... (Geri kalan veri işleme kısmı aynı) ...

            if 'errors' in res_json:
                print(f"❌ GRAPHQL HATASI: {res_json['errors']}")
                return []

            raw_data = res_json['data']['allOpportunity']['data']
            projects = []

            for op in raw_data:
                # Veri işleme
                spec = op.get('specifics_info') or {}
                curr = spec.get('salary_currency') or {}
                salary_str = f"{spec.get('salary', '')} {curr.get('alphabetic_code', '')}".strip()

                projects.append(OGTProject(
                    op_id=str(op['id']),
                    title=op.get('title', ''),
                    description=op.get('description', ''),
                    role_info=op.get('role_info', ''),
                    organisation=(op.get('organisation') or {}).get('name', ''),
                    country=(op.get('home_mc') or {}).get('name', ''),
                    city=(op.get('home_lc') or {}).get('name', ''),
                    status="open",
                    salary=salary_str,
                    duration=(op.get('opportunity_duration_type') or {}).get('duration_type', ''),
                    link=f"https://aiesec.org/opportunity/global-talent/{op['id']}",
                    backgrounds=[b['constant_name'] for b in op.get('backgrounds', [])],
                    skills=[s['constant_name'] for s in op.get('skills', [])]
                ))

            print(f"✅ {len(projects)} proje başarıyla işlendi.")
            return projects

        except Exception as e:
            # İşte Python'un beklediği o 'except' bloğu
            print(f"❌ BAĞLANTI HATASI: {e}")
            return []