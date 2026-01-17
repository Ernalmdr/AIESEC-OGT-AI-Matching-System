import gspread
import os
from google.oauth2.service_account import Credentials
from datetime import datetime


class GoogleSheetsRepository:
    def __init__(self):
        # Yetki Kapsamları
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Dosya yolu kontrolü
        self.creds_file = "credentials.json"
        self.client = None

        # Eğer dosya varsa bağlan
        if os.path.exists(self.creds_file):
            try:
                credentials = Credentials.from_service_account_file(
                    self.creds_file, scopes=self.scopes
                )
                self.client = gspread.authorize(credentials)
            except Exception as e:
                print(f"Google Sheets Bağlantı Hatası: {e}")
        else:
            print("⚠️ UYARI: 'credentials.json' bulunamadı. Sheets kaydı yapılamaz.")

    def log_match(self, sheet_name, candidate_name, project_title, company, country, score, strategy):
        """
        Analiz sonucunu tabloya ekler.
        """
        if not self.client:
            return False

        try:
            # Tabloyu aç (Eğer yoksa hata verir, oluşturmaz)
            sheet = self.client.open(sheet_name).sheet1

            # Tarih
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            # Satır Ekle
            row = [date_str, candidate_name, project_title, company, country, score, strategy]
            sheet.append_row(row)
            return True

        except Exception as e:
            print(f"Kayıt Hatası: {e}")
            return False