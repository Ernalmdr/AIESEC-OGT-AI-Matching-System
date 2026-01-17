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
        Sen AIESEC Global Talent Programı için "Headhunter" (Yetenek Avcısı) gibi düşünen profesyonel bir yapay zeka asistanısın.

        ### 👤 ADAY PROFİLİ
        - İsim: {ep.full_name}
        - Bölüm: {ep.background}
        - Yetenekler: {", ".join(ep.skills)}
        - CV Özeti: {cv_content[:1500] if cv_content else "CV Yok."}

        ### 🏢 ANALİZ EDİLECEK PROJELER
        {projects_text}

        ### 📋 GÖREVİN
        Yukarıdaki projelerin her birini aday ile eşleştir ve aşağıdaki formatta bir JSON listesi oluştur.

        WhatsApp Mesajı Kuralları:
        1. Samimi, enerjik ve profesyonel ol (AIESEC tonu).
        2. Adayın ismini kullan.
        3. Projenin en vurucu özelliğini (Maaş, Ülke veya Şirket) hemen başta söyle.
        4. "Senin profiline çok uygun çünkü..." kalıbını kullanarak kişiselleştir.
        5. Sorulacak bir soru ile bitir (Örn: "Detayları konuşalım mı?").
        6. Emoji kullan 🚀🌍💼

        JSON FORMATI (Sadece bu listeyi döndür):
        [
            {{
                "project_index": 0,
                "technical_match": "CV'deki [Yetenek] ile projedeki [Gereksinim] tam uyuşuyor...",
                "culture_fit": "Adayın geçmişi [Ülke] çalışma kültürüne...",
                "pain_points": "Vize süreci uzun olabilir veya deneyim az kalabilir...",
                "sales_pitch": "Bu proje sana [Şirket] bünyesinde global bir network kazandırır...",
                "interview_q": "Daha önce [Konu] ile ilgili zor bir durumu nasıl yönettin?",
                "score": 85,
                "whatsapp_msg": "Selam [Ad]! 🚀 [Ülke]'de harika bir [Pozisyon] fırsatı var..."
            }}
        ]
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