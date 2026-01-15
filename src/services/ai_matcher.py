import os
from google import genai
from src.core.models import OGTProject, ExchangeParticipant

class AIMatcher:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        # Yeni başlatma şekli
        self.client = genai.Client(api_key=api_key)

    def generate_match_report(self, ep: ExchangeParticipant, project: OGTProject) -> str:
        prompt = f"Aday {ep.full_name} ile {project.title} projesini analiz et..."
        try:
            # Yeni kütüphanede metod yapısı
            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Gemini Hatası: {str(e)}"