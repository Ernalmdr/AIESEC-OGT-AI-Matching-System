import os
import requests
import json
import time
import re
from src.utils.config_manager import ConfigManager


class AIMatcher:
    def __init__(self):
        # ConfigManager kullanarak güvenli key alımı (veya os.getenv)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-3-flash-preview"  # Daha hızlı ve yeni model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

    def generate_batch_report(self, ep, projects, cv_content=""):
        """
        360 Derece Analiz: Teknik, Kültürel, Vize ve Satış Stratejisi
        """

        projects_text = ""
        for i, p in enumerate(projects):
            # JD Scraper ile çekilen uzun açıklamayı kullanıyoruz
            # Eğer açıklama çok uzunsa ilk 1500 karakteri alıp token tasarrufu yapıyoruz
            desc_preview = p.description[:1500] if p.description else "Detay yok."

            projects_text += f"""
            --- PROJE {i} ---
            - Başlık: {p.title}
            - Kurum: {p.organisation}
            - Ülke/Şehir: {p.country} / {p.city}
            - Maaş: {p.salary}
            - Süre: {p.duration}
            - İş Tanımı (Özet): {desc_preview}
            """

        prompt = f"""
                Sen AIESEC Global Talent programı için hem teknik bir İşe Alım Uzmanı (Recruiter) hem de usta bir Satışçısın.

                GÖREV: Aşağıdaki adayı ve projeyi analiz et. Önce teknik uygunluğunu değerlendir, sonra bu projeyi adaya satmak için bana koz ver.

                ADAY VERİLERİ:
        	- İsim: {ep.full_name}
                - Profil: {ep.background}
                - Yetenekler: {", ".join(ep.skills)}
                - CV Detayı: {cv_content if cv_content else "CV yok (Sadece profile odaklan)"}

        	### 🏢 ANALİZ EDİLECEK PROJELER
                {projects_text}

    

                İSTENEN JSON ÇIKTISI:
                {{


        	    "project_index": 0,
                    "technical_match": "CV'deki [Yetenek] ile projedeki [Gereksinim] tam uyuşuyor...",
                    "culture_fit": "Adayın geçmişi [Ülke] çalışma kültürüne...",
                    "score": (0-100 arası gerçekçi uyum puanı),

                    "suitability_analysis": "OBJEKTİF ANALİZ: Aday bu işi teknik olarak yapabilir mi? Hangi yeteneği tam uyuyor, hangisi eksik? 'Adayın X tecrübesi var ama Y konusunda zorlanabilir' gibi dürüst ve net bir teknik değerlendirme yaz.",

                    "sales_pitch": "VİZYON SATIŞI: Adayı heyecanlandıracak, teknik detaylardan çok 'kariyerine katacağı değere' odaklanan 2-3 cümlelik motivasyon konuşması.",

                    "pain_points": "İKNA KOZU (PAIN POINT): Adayın profilindeki eksikleri veya kariyerindeki boşlukları (örn: yurtdışı deneyimi yok, İngilizcesi teorik kalmış vb.) tespit et. 'Bak senin X eksiğin var, bu proje tam da bunu kapatıyor, gitmezsen geride kalırsın' diyebileceğimiz, adayı 'Evet buna ihtiyacım var' dedirtecek 2 kritik koz.",

                    "whatsapp_msg": "Adaya projeyi atan, samimi, harekete geçirici kısa mesaj."
                }}
                {{
                "project_index": 2,
                ... (Diğer projeler için aynı format)
                }}
                """

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        # --- Retry Logic ---
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(self.url, json=payload, timeout=90)  # Süreyi uzattık

                if response.status_code == 200:
                    result = response.json()
                    if "candidates" in result:
                        raw = result['candidates'][0]['content']['parts'][0]['text']
                        # JSON bloğunu temizle (Markdown ```json ... ``` kısımlarını siler)
                        clean_json = raw.replace("```json", "").replace("```", "").strip()
                        match = re.search(r"\[.*\]", clean_json, re.DOTALL)
                        if match: return json.loads(match.group(0))

                elif response.status_code == 429:
                    time.sleep(10)
                    continue
                else:
                    print(f"Hata Kodu: {response.status_code}")

            except Exception as e:
                print(f"Bağlantı Hatası: {e}")
                time.sleep(2)

        return []

    def extract_keywords_from_cv(self, cv_text):
        """
        CV metninden gereksiz kelimeleri atıp sadece teknik yetenekleri çeker.
        """
        prompt = f"""
        Sen uzman bir HR asistanısın. Aşağıdaki CV metnini analiz et.
        Bana adayın en güçlü olduğu 15 teknik yeteneği (Hard Skills) ve alan bilgisini (Domain Knowledge) listele.

        Kurallar:
        1. Sadece İngilizce kelimeler kullan.
        2. "Teamwork", "Hardworking" gibi soft skill'leri EKLEME.
        3. "University", "Istanbul", "Address" gibi gereksiz bilgileri EKLEME.
        4. Çıktı sadece ve sadece virgülle ayrılmış kelimeler olsun.

        Örnek Çıktı: Python, Django, Marketing, SEO, Google Ads, Java, SQL

        CV Metni:
        {cv_text[:2000]}
        """

        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(self.url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                raw_text = result['candidates'][0]['content']['parts'][0]['text']
                # Virgülle ayrılmış metni listeye çevir ve temizle
                keywords = [k.strip().lower() for k in raw_text.split(',')]
                return keywords
        except Exception as e:
            print(f"Keyword Extraction Hatası: {e}")

        return []  # Hata olursa boş dön