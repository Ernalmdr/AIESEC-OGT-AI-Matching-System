import streamlit as st
import sys
import os
import urllib.parse
import PyPDF2
import pandas as pd
import random
import json
import asyncio
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util

# Servis ve Repo Importları
try:
    from src.repositories.podio_repo import PodioRepository
    from src.repositories.expa_repo import ExpaRepository
    from src.services.ai_matcher import AIMatcher
    from src.services.jd_scraper import JDScraper
    from src.repositories.google_sheets_repo import GoogleSheetsRepository
    from src.services.pdf_generator import PDFReportGenerator
except ImportError as e:
    st.error(f"⚠️ Kritik Hata: Dosyalar bulunamadı! ({e})")
    st.stop()

# --- 1. AYARLAR & SECRETS ---
st.set_page_config(page_title="OGT AI Matcher", layout="wide", page_icon="🤖")
load_dotenv()

try:
    if hasattr(st, "secrets") and st.secrets:
        for key, value in st.secrets.items():
            os.environ[key] = str(value)
        if "GOOGLE_CREDENTIALS" in st.secrets:
            with open("credentials.json", "w") as f:
                f.write(st.secrets["GOOGLE_CREDENTIALS"])
except Exception:
    pass


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')


def main():
    st.title("🤖 AIESEC OGT Operasyon Paneli v2.1")

    # --- SESSION STATE ---
    if 'applicants' not in st.session_state: st.session_state['applicants'] = []
    if 'project_offset' not in st.session_state: st.session_state.project_offset = 0
    if 'filtered_projects_cache' not in st.session_state: st.session_state.filtered_projects_cache = []
    if 'ai_results_cache' not in st.session_state: st.session_state.ai_results_cache = {}

    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Ayarlar")
    if st.sidebar.button("🧹 Sıfırla"):
        st.session_state.clear()
        st.rerun()

    # --- YAN MENÜ: PODİO YAPILANDIRMASI ---
    st.sidebar.header("🎯 Liste ve Program Seçimi")

    # 1. Programlara göre App ID ve View ID tanımlamaları
    # Buradaki rakamları kendi Podio ortamındaki gerçek ID'lerle doldurmalısın.
    view_config = {
        "GTe Sign Up": {"app_id": "24908517", "view_id": "61629575"},
        "GTe Contacted": {"app_id": "24908517", "view_id": "61629576"},
        "GTa Sign Up": {"app_id": "23409870", "view_id": "61478954"},
        "GTa Contacted": {"app_id": "23409870", "view_id": "61478957"},
        "GV Sign Up": {"app_id": "23409869", "view_id": "61629578"},
        "GV Contacted": {"app_id": "23409869", "view_id": "61629579"}
    }

    # 2. Seçili ayarları hafızada tutmak için session_state (Varsayılan olarak GTe Sign Up)
    if 'active_config' not in st.session_state:
        st.session_state.active_config = view_config["GTa Contacted"]
        st.session_state.active_name = "GTa Contacted"

    # 3. Butonları 2'li kolonlar halinde oluştur
    cols = st.sidebar.columns(2)
    for i, (name, config) in enumerate(view_config.items()):
        if cols[i % 2].button(name, use_container_width=True):
            st.session_state.active_config = config
            st.session_state.active_name = name
            st.toast(f"Seçildi: {name}")

    # 4. Bilgilendirme Ekranı (Hangi ID'lerin aktif olduğunu görmek için)
    with st.sidebar.expander("ℹ️ Aktif ID Detayları"):
        st.caption(f"Program: {st.session_state.active_name}")
        st.caption(f"App ID: {st.session_state.active_config['app_id']}")
        st.caption(f"View ID: {st.session_state.active_config['view_id']}")

    # 5. Adayları Çek Butonu
    if st.sidebar.button("📦 Adayları Çek", type="primary", use_container_width=True):
        with st.spinner(f"{st.session_state.active_name} verileri çekiliyor..."):
            try:
                repo = PodioRepository()
                # session_state içindeki güncel app_id ve view_id'yi kullanıyoruz
                apps = repo.fetch_applicants(
                    app_id=st.session_state.active_config['app_id'],
                    view_id=st.session_state.active_config['view_id']
                )
                st.session_state['applicants'] = apps
                st.sidebar.success(f"✅ {len(apps)} aday yüklendi!")
            except Exception as e:
                st.sidebar.error(f"Bağlantı Hatası: {e}")

    st.sidebar.divider()
    st.sidebar.header("🎯 Gelişmiş Filtreler")
    f_country = st.sidebar.text_input("🌍 Ülke")
    f_field = st.sidebar.text_input("💼 Departman")
    f_duration = st.sidebar.selectbox("⏳ Süre", ["Farketmez", "Short", "Medium", "Long"])
    f_paid_only = st.sidebar.checkbox("💰 Sadece Maaşlı Projeler")

    forbidden_lcs_input = st.sidebar.text_input("🛡️ Yasaklı LC'ler", value="M.A, H.E")
    forbidden_lcs = [lc.strip().lower() for lc in forbidden_lcs_input.split(",") if lc.strip()]

    # --- ANA EKRAN ---
    if st.session_state['applicants']:
        names = [a.full_name for a in st.session_state['applicants']]
        selected_name = st.selectbox("Aday Seç:", names)

        # Aday değişince temizle
        if st.session_state.get('last_selected_candidate') != selected_name:
            st.session_state.ai_results_cache = {}
            st.session_state.filtered_projects_cache = []
            st.session_state.project_offset = 0
            st.session_state.last_selected_candidate = selected_name
            st.rerun()

        ep = next((a for a in st.session_state['applicants'] if a.full_name == selected_name), None)

        if ep:
            st.info(f"👤 **{ep.full_name}** | 🎓 {ep.background or 'Bölüm Yok'} | 📧 {ep.email}")

            uploaded_file = st.file_uploader("📄 CV Yükle (PDF)", type="pdf")
            cv_text = ""
            if uploaded_file:
                pdf = PyPDF2.PdfReader(uploaded_file)
                for p in pdf.pages: cv_text += p.extract_text()
                st.caption("✅ CV okundu.")

            col_b1, col_b2 = st.columns(2)
            btn_start = col_b1.button("🚀 Eşleşmeleri Bul")
            btn_more = col_b2.button("🔄 Sonraki 3 Proje")

            matcher = AIMatcher()
            expa = ExpaRepository()
            scraper = JDScraper()

            if btn_start:
                st.session_state.project_offset = 0
                st.session_state.ai_results_cache = {}
                with st.spinner("🌍 EXPA projeleri asenkron çekiliyor..."):
                    try:
                        all_projects = asyncio.run(expa.fetch_data_async())

                        filtered = []
                        for p in all_projects:
                            # 1. Yasaklı LC ve Türkiye Filtresi
                            country_check = (p.country or "").lower()
                            if "turkey" in country_check or "türkiye" in country_check: continue

                            city_check = (p.city or "").lower()
                            if any(forbidden in city_check for forbidden in forbidden_lcs): continue

                            # 2. Süre & Maaş Filtresi
                            if f_duration != "Farketmez" and f_duration.lower() not in (
                                    p.duration or "").lower(): continue
                            if f_paid_only and (not p.salary or p.salary.startswith("0")): continue

                            # 3. Metin Filtresi
                            search_text = (p.title + " " + p.organisation).lower()
                            if f_country and f_country.lower() not in country_check: continue
                            if f_field and f_field.lower() not in search_text: continue

                            filtered.append(p)

                        if filtered:
                            embedder = load_embedding_model()
                            candidate_text = f"{ep.background} {' '.join(ep.skills)}"
                            candidate_emb = embedder.encode(candidate_text, convert_to_tensor=True)

                            proj_texts = [f"{p.title} {p.organisation} {p.description[:300]}" for p in filtered]
                            proj_embs = embedder.encode(proj_texts, convert_to_tensor=True)

                            scores = util.cos_sim(candidate_emb, proj_embs)[0]
                            scored = []
                            for i, p in enumerate(filtered):
                                final_score = float(scores[i]) * 100 + random.randint(0, 3)
                                if final_score > 20: scored.append((final_score, p))

                            scored.sort(key=lambda x: x[0], reverse=True)
                            st.session_state.filtered_projects_cache = [x[1] for x in scored]
                            st.success(f"🚀 {len(filtered)} proje tarandı.")
                        else:
                            st.error("Uygun proje bulunamadı.")
                    except Exception as e:
                        st.error(f"Hata: {e}")

            if btn_more:
                if st.session_state.filtered_projects_cache:
                    st.session_state.project_offset = (st.session_state.project_offset + 3) % len(
                        st.session_state.filtered_projects_cache)

            # --- SONUÇLARI GÖSTER ---
            cache = st.session_state.filtered_projects_cache
            offset = st.session_state.project_offset

            if cache:
                batch = cache[offset: offset + 3]
                batch_key = f"batch_{offset}"

                if batch_key not in st.session_state.ai_results_cache:
                    with st.spinner("🧠 AI Analiz Ediyor..."):
                        # Detayları çek
                        for p in batch:
                            if len(p.description) < 200 and p.link:
                                try:
                                    p.description = scraper.fetch_description(p.link)
                                except:
                                    pass

                        # Asenkron Analiz
                        # ÖNEMLİ: ai_matcher.py içindeki analyze_candidate_async listesi dönmeli
                        results = asyncio.run(matcher.analyze_candidate_async(ep, batch, cv_text))
                        if isinstance(results, dict) and "error" in results:
                            st.error(results["error"])
                            st.session_state.ai_results_cache[batch_key] = []
                        else:
                            st.session_state.ai_results_cache[batch_key] = results

                results = st.session_state.ai_results_cache.get(batch_key, [])

                if results:
                    for i, res in enumerate(results):
                        # AI bazen yanlış index dönebilir, güvenli seçim yapıyoruz
                        p_idx = res.get('project_index', i)
                        p = batch[p_idx] if p_idx < len(batch) else batch[min(i, len(batch) - 1)]

                        with st.expander(f"📌 {p.title} - {p.organisation} (Uyum: %{res.get('score', 0)})",
                                         expanded=True):
                            t1, t2 = st.tabs(["🧠 Analiz", "💬 Aksiyon"])
                            with t1:
                                st.write(f"**Teknik Analiz:** {res.get('suitability_analysis')}")
                                st.success(f"**Satış:** {res.get('sales_pitch')}")
                                st.warning(f"**İkna Kozu:** {res.get('pain_points')}")
                                with st.popover("📄 Detaylı İş Tanımı"):
                                    st.write(p.description)
                            with t2:
                                phone = getattr(ep, 'phone', '').replace(" ", "").replace("+", "")
                                msg = urllib.parse.quote(res.get('whatsapp_msg', ''))
                                st.link_button("📱 WhatsApp", f"https://wa.me/{phone}?text={msg}")

                                # Kayıt Butonu
                                if st.button(f"📝 Kaydet", key=f"save_{offset}_{i}"):
                                    try:
                                        # Sheets Kaydı
                                        sheets = GoogleSheetsRepository()
                                        sheets.log_match("Analiz_Log", ep.full_name, p.title, p.organisation, p.country,
                                                         res.get('score'), res.get('sales_pitch'))
                                        # Podio Kaydı
                                        repo_podio = PodioRepository()
                                        comment = f"AI Analizi: %{res.get('score')} uyum. Strateji: {res.get('sales_pitch')}"
                                        repo_podio.add_comment(ep.ep_id, comment)
                                        st.toast("Başarıyla kaydedildi!")
                                    except Exception as e:
                                        st.error(f"Kayıt Hatası: {e}")
    else:
        st.info("👈 Podio'dan adayları çekerek başlayın.")


if __name__ == "__main__":
    main()
