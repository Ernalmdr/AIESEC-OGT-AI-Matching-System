# 🤖 AIESEC OGT AI Matching System

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![AI Model](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

**AIESEC Outgoing Global Talent (OGT)** operasyonları için geliştirilmiş, yapay zeka destekli akıllı aday-proje eşleştirme asistanı.

Bu sistem, **Podio** üzerindeki adayları ve **EXPA** üzerindeki fırsatları analiz eder, **Semantik Arama** ve **LLM (Google Gemini)** kullanarak en uygun eşleşmeleri bulur ve operasyon süreçlerini hızlandırır.

---

## 🚀 Özellikler

* **Veri Entegrasyonu:**
    * 📥 **Podio API:** Adayların profil, yetenek ve geçmiş verilerini otomatik çeker.
    * 🌍 **EXPA (GIS) API:** AIESEC global veritabanındaki aktif projeleri filtreleyerek çeker.
    * 📊 **Google Sheets:** Eşleşme analizlerini ve operasyonel kayıtları tablolara işler.
* **Yapay Zeka Motoru:**
    * 🧠 **Hibrit Eşleştirme:** `Sentence Transformers` ile anlamsal, `Google Gemini` ile stratejik analiz yapar.
    * 🕸️ **Akıllı Scraping:** Proje açıklaması eksikse ilgili linkten veriyi otomatik tamamlar.
* **Aksiyon ve Raporlama:**
    * 📄 **PDF Raporu:** Adaya özel, profesyonel eşleşme raporları üretir.
    * 💬 **Satış Koçluğu:** Operasyon üyesine "Nasıl satarsın?", "İkna kozları neler?" gibi stratejiler sunar.
    * 🖥️ **Streamlit Dashboard:** Kullanıcı dostu, interaktif web arayüzü.

---

## 🛠️ Kullanılan Teknolojiler

* **Dil:** Python 3.11+
* **Arayüz:** Streamlit
* **AI & NLP:** Google Gemini API, Sentence-Transformers
* **Veri Kaynakları:** Podio API, GraphQL (EXPA), Google Sheets API (gspread)
* **Araçlar:** BeautifulSoup4, FPDF2, Python-Dotenv

---

## 📂 Proje Yapısı

```text
AIESEC-OGT-AI-Matching-System/
├── .devcontainer/       # DevContainer yapılandırması
├── .streamlit/          # Streamlit gizli anahtarları
├── src/
│   ├── core/            # Veri modelleri (Entity'ler: EP, Project vb.)
│   ├── interfaces/      # Soyut sınıflar (Interface)
│   ├── repositories/    # Veri erişim katmanı (Podio, Expa, Sheets)
│   ├── services/        # İş mantığı (AI Matcher, PDF Gen, Scraper)
│   └── utils/           # Yardımcı araçlar (Config)
├── tests/               # Bağlantı testleri
├── app.py               # Streamlit Arayüzü (Web App)
├── main.py              # CLI / Bot Otomasyonu
├── requirements.txt     # Kütüphane bağımlılıkları
└── README.md            # Dokümantasyon
```
---
## Sanal Ortam Oluşturun Python kütüphanelerinin çakışmaması için sanal ortam kurun:
```bash
# Windows için:
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux için:
python3 -m venv .venv
source .venv/bin/activate
```
---
## Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```
---
## ⚙️ Yapılandırma (.env Ayarları) 
```TOML
# --- PODIO AYARLARI ---
PODIO_CLIENT_ID=buraya_client_id_gelecek
PODIO_CLIENT_SECRET=buraya_client_secret_gelecek
PODIO_USERNAME=podio_mail_adresiniz
PODIO_PASSWORD=podio_sifreniz

# --- EXPA (AIESEC) AYARLARI ---
EXPA_ACCESS_TOKEN=buraya_expa_token_gelecek

# --- GOOGLE AI ---
GEMINI_API_KEY=buraya_gemini_api_key_gelecek

# --- GOOGLE SHEETS (Opsiyonel) ---
GOOGLE_CREDENTIALS=credentials.json
```
Not: credentials.json dosyasını proje ana dizinine eklemeyi unutmayın.
---
## 🤝 Katkıda Bulunma
1.Bu repoyu fork'layın.

2.Yeni bir branch oluşturun (git checkout -b feature/YeniOzellik).

3.Değişikliklerinizi commit'leyin (git commit -m 'Yeni özellik eklendi').

4.Branch'inizi push'layın (git push origin feature/YeniOzellik).

5.Bir Pull Request oluşturun.

---
## ▶️ Kullanım
Kurulum tamamlandıktan sonra uygulamayı iki farklı modda çalıştırabilirsiniz:

## 1. Arayüz Modu (Operasyon Paneli)
Görsel arayüz üzerinden aday seçimi ve analiz yapmak için:
```bash
streamlit run app.py
```
Tarayıcınızda http://localhost:8501 adresi açılacaktır.
## 2. Bot Modu (Otomatik Tarama)
Arkaplanda çalışıp başvuruları taramak ve otomatik işlem yapmak için:
```bash
python main.py
```
