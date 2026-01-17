import requests
import json
import os
import streamlit as st
from dotenv import load_dotenv
from src.core.models import ExchangeParticipant

load_dotenv()

class PodioRepository:
    def __init__(self):
        # Yardımcı fonksiyon: Hem Secrets hem .env kontrol eder
        def get_conf(key):
            if hasattr(st, "secrets") and key in st.secrets:
                return st.secrets[key]
            return os.getenv(key)

        self.client_id = get_conf("PODIO_CLIENT_ID")
        self.client_secret = get_conf("PODIO_CLIENT_SECRET")
        self.username = get_conf("PODIO_USERNAME")
        self.password = get_conf("PODIO_PASSWORD")

        self.auth_url = "https://podio.com/oauth/token"
        self.access_token = None

        # Bilgiler eksikse hata vermemesi için kontrol, ama log basar
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            print("⚠️ Podio bilgileri eksik (Secrets veya .env kontrol edin).")

    def _get_access_token(self):
        payload = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        try:
            # Timeout ekleyerek sonsuz döngüden kaçınma
            response = requests.post(self.auth_url, data=payload, timeout=30)
            
            if response.status_code != 200:
                # Hata detayını string'e çevirip fırlat
                raise Exception(f"Giriş Başarısız! Status: {response.status_code}, Mesaj: {response.text}")
                
            return response.json().get("access_token")
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Podio Bağlantı Hatası: {e}")

    def add_comment(self, item_id, comment_text):
        """
        Belirtilen Item ID'ye yorum yazar.
        """
        if not self.access_token:
            self.access_token = self._get_access_token()

        url = f"https://api.podio.com/comment/item/{item_id}"

        headers = {
            "Authorization": f"OAuth2 {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {"value": comment_text}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            # Token süresi dolduysa (401), yenileyip tekrar dene
            if response.status_code == 401:
                self.access_token = self._get_access_token()
                headers["Authorization"] = f"OAuth2 {self.access_token}"
                response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                raise Exception(f"Yorum Hatası ({response.status_code}): {response.text}")

            return True
        except Exception as e:
            print(f"Yorum eklenirken hata: {e}")
            return False

    def fetch_applicants(self, app_id, view_id=None):
        """
        Başvuruları çeker.
        """
        if not self.access_token:
            try:
                self.access_token = self._get_access_token()
            except Exception as e:
                st.error(f"Podio Token Hatası: {e}")
                return []

        base_url = f"https://api.podio.com/item/app/{app_id}/filter/"
        url = f"{base_url}{view_id}/" if view_id else base_url

        headers = {
            "Authorization": f"OAuth2 {self.access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json={"limit": 50}, timeout=30)

            if response.status_code == 401:
                self.access_token = self._get_access_token()
                headers["Authorization"] = f"OAuth2 {self.access_token}"
                response = requests.post(url, headers=headers, json={"limit": 50}, timeout=30)

            if response.status_code != 200:
                st.error(f"Podio Veri Çekme Hatası: {response.status_code}")
                return []

            data = response.json()
            items = data.get("items") or []

            applicants = []

            for item in items:
                fields = item.get("fields") or []
                
                # Yorum için gerekli item_id
                ep_id_long = str(item.get("item_id"))

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
                    # Podio value bazen dict bazen direkt değer döner
                    raw_val = val0.get("value") if isinstance(val0, dict) else val0

                    # Etiket eşleştirme (Label isimleri Podio'nuzla aynı olmalı)
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
                            bg_university = str(raw_val)
                    elif label == "Career":
                        bg_career = str(raw_val)
                    # Yetenekleri yakalama (Skill, Language, English vb. içeren tüm alanlar)
                    elif any(x in label.lower() for x in ["skill", "yetenek", "language", "english", "passport"]):
                        for v in values:
                            if isinstance(v, dict) and "value" in v:
                                val_content = v["value"]
                                if isinstance(val_content, dict):
                                    skills.append(val_content.get("text", ""))
                                else:
                                    skills.append(str(val_content))
                            elif isinstance(v, dict) and "text" in v: # Bazen direkt text alanı olabilir
                                skills.append(v["text"])
                            else:
                                skills.append(str(v))

                final_bg = []
                if bg_career: final_bg.append(str(bg_career))
                if bg_university: final_bg.append(str(bg_university))
                background_str = " - ".join(final_bg) if final_bg else "Belirtilmemiş"

                ep = ExchangeParticipant(
                    ep_id=ep_id_long,
                    full_name=name,
                    email=email,
                    background=background_str,
                    skills=skills,
                    phone=phone
                )
                applicants.append(ep)

            return applicants

        except Exception as e:
            st.error(f"Podio İşlem Hatası: {e}")
            return []
