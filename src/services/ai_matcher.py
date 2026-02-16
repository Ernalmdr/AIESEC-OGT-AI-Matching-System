import os
import httpx
import requests
import json
import time
import re
import asyncio
from src.utils.config_manager import ConfigManager


class AIMatcher:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # ÖNEMLİ: gemini-3-flash-preview bazen stabil olmayabilir, 1.5-flash en güvenlisidir
        self.model_name = "gemini-1.5-flash"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

    async def analyze_candidate_async(self, ep, projects, cv_content=""):
        """Tek bir aday için projeleri asenkron analiz eder ve liste döndürür."""

        projects_text = ""
        for i, p in enumerate(projects):
            desc_preview = p.description[:1500] if p.description else "Detay yok."
            projects_text += f"""
            --- PROJE INDEX: {i} ---
            - Başlık: {p.title}
            - Kurum: {p.organisation}
            - Ülke/Şehir: {p.country} / {p.city}
            - Maaş: {p.salary}
            - İş Tanımı: {desc_preview}
            """

        # Prompt'ta JSON formatını LISTE ([ ]) olarak zorunlu kılıyoruz
        prompt = f"""
        Sen AIESEC Global Talent programı için teknik bir İşe Alım Uzmanı ve Satışçısın.
        Adayı ve sunulan {len(projects)} projeyi analiz et. 

        ADAY: {ep.full_name}
        PROFİL: {ep.background}
        YETENEKLER: {", ".join(ep.skills)}
        CV: {cv_content[:2000] if cv_content else "Yok"}

        PROJELER:
        {projects_text}

        GÖREV: Her bir proje için analiz yap ve sonucu MUTLAKA bir JSON LISTESI ([...]) olarak dön.

        FORMAT:
        [
          {{
            "project_index": 0,
            "score": 85,
            "suitability_analysis": "Teknik analiz...",
            "sales_pitch": "Adaya satış konuşması...",
            "pain_points": "İkna kozları...",
            "whatsapp_msg": "Kısa mesaj..."
          }},
          ...
        ]
        """

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.url, json=payload, timeout=90.0)
                if response.status_code == 200:
                    result = response.json()
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']

                    # --- GÜÇLÜ JSON TEMİZLEME ---
                    # Markdown bloklarını temizle
                    clean_text = re.sub(r"```json|```", "", raw_text).strip()
                    # Liste başlangıcını ve bitişini bul ([ ile başlar ] ile biter)
                    match = re.search(r"\[.*\]", clean_text, re.DOTALL)

                    if match:
                        return json.loads(match.group(0))
                    else:
                        # Eğer liste değil de tek bir obje döndüyse listeye sar
                        obj_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
                        if obj_match:
                            return [json.loads(obj_match.group(0))]

                print(f"API Hatası: {response.status_code}")
                return []
            except Exception as e:
                print(f"Async Analiz Hatası: {e}")
                return []

    async def run_parallel_analysis(self, applicants, projects, cv_content=""):
        """Tüm adaylar için analizleri paralel olarak başlatır."""
        tasks = []
        for ep in applicants:
            tasks.append(self.analyze_candidate_async(ep, projects, cv_content))

        results = await asyncio.gather(*tasks)
        return results

    def extract_keywords_from_cv(self, cv_text):
        """CV metninden yetenekleri ayıklar (Senkron)."""
        prompt = f"Extract top 10 technical skills from this CV as a comma-separated list: {cv_text[:2000]}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(self.url, json=payload, timeout=15)
            if response.status_code == 200:
                raw = response.json()['candidates'][0]['content']['parts'][0]['text']
                return [k.strip().lower() for k in raw.split(',')]
        except:
            pass
        return []