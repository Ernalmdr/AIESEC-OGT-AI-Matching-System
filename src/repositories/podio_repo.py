import requests
import json
import os
from dotenv import load_dotenv
from src.core.models import ExchangeParticipant

load_dotenv()


class PodioRepository:
    def __init__(self):
        self.client_id = os.getenv("PODIO_CLIENT_ID")
        self.client_secret = os.getenv("PODIO_CLIENT_SECRET")
        self.username = os.getenv("PODIO_USERNAME")
        self.password = os.getenv("PODIO_PASSWORD")

        self.auth_url = "https://podio.com/oauth/token"
        self.access_token = None

        if not self.client_id or not self.client_secret or not self.username or not self.password:
            raise ValueError("❌ HATA: .env dosyasında eksik bilgiler var.")

    def _get_access_token(self):
        payload = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        try:
            response = requests.post(self.auth_url, data=payload, timeout=30)
            if response.status_code != 200:
                raise Exception(f"Giriş Başarısız! Hata: {response.text}")
            return response.json().get("access_token")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Podio Bağlantı Hatası: {e}")

    def add_comment(self, item_id, comment_text):
        """
        Belirtilen Item ID'ye (Uzun ID) yorum yazar.
        """
        if not self.access_token:
            self.access_token = self._get_access_token()

        # Podio API: Yorum Ekleme Endpoint'i
        url = f"https://api.podio.com/comment/item/{item_id}"

        headers = {
            "Authorization": f"OAuth2 {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {"value": comment_text}

        try:
            response = requests.post(url, headers=headers, json=payload)

            # Eğer token süresi dolduysa (401), yenileyip tekrar dene
            if response.status_code == 401:
                self.access_token = self._get_access_token()
                headers["Authorization"] = f"OAuth2 {self.access_token}"
                response = requests.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                raise Exception(f"Yorum Hatası ({response.status_code}): {response.text}")

            return True
        except Exception as e:
            raise Exception(f"Podio Yorum Hatası: {e}")

    def fetch_applicants(self, app_id, view_id=None):
        if not self.access_token:
            self.access_token = self._get_access_token()

        base_url = f"https://api.podio.com/item/app/{app_id}/filter/"
        url = f"{base_url}{view_id}/" if view_id else base_url

        headers = {
            "Authorization": f"OAuth2 {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json={"limit": 50})

        if response.status_code == 401:
            self.access_token = self._get_access_token()
            headers["Authorization"] = f"OAuth2 {self.access_token}"
            response = requests.post(url, headers=headers, json={"limit": 50})

        if response.status_code != 200:
            raise Exception(f"Hata: {response.status_code} {response.text}")

        data = response.json()
        items = data.get("items") or []

        applicants = []

        for item in items:
            fields = item.get("fields") or []

            # ÖNEMLİ DEĞİŞİKLİK: Yorum yazabilmek için 'item_id' (Uzun ID) kullanıyoruz.
            # Merak etme, linkler bu ID ile de çalışır.
            ep_id = str(item.get("item_id"))

            name = item.get("title", "İsimsiz Aday")
            email = "Mail Bulunamadı"
            phone = ""
            bg_university = ""
            bg_career = ""
            skills = []

            for f in fields:
                label = f.get("label", "")
                if not label: continue

                values = f.get("values") or []
                if not values: continue

                val0 = values[0]
                raw_val = val0.get("value") if isinstance(val0, dict) else val0

                if label == "EP Name":
                    name = raw_val
                elif label == "EP Email":
                    email = raw_val
                elif label == "EP Phone Number":
                    phone = raw_val
                elif label == "University":
                    if isinstance(raw_val, dict):
                        bg_university = raw_val.get("text", "")
                    else:
                        bg_university = raw_val
                elif label == "Career":
                    bg_career = raw_val
                elif any(x in label.lower() for x in ["skill", "yetenek", "language", "english", "passport"]):
                    for v in values:
                        if isinstance(v, dict) and "value" in v:
                            val_content = v["value"]
                            if isinstance(val_content, dict):
                                skills.append(val_content.get("text", ""))
                            else:
                                skills.append(str(val_content))

            final_bg = []
            if bg_career: final_bg.append(str(bg_career))
            if bg_university: final_bg.append(str(bg_university))
            background_str = " - ".join(final_bg) if final_bg else "Belirtilmemiş"

            ep = ExchangeParticipant(
                ep_id=ep_id,
                full_name=name,
                email=email,
                background=background_str,
                skills=skills,
                phone=phone
            )
            applicants.append(ep)

        return applicants