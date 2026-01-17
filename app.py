import streamlit as st
import sys
import os
import urllib.parse
import PyPDF2
import pandas as pd
import random
import json
from dotenv import load_dotenv

# --- 1. AYARLAR ---
st.set_page_config(page_title="OGT AI Matcher", layout="wide", page_icon="🤖")

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importlar
try:
    from src.repositories.podio_repo import PodioRepository
    from src.repositories.expa_repo import ExpaRepository
    from src.services.ai_matcher import AIMatcher
    from src.services.jd_scraper import JDScraper
    from src.repositories.google_sheets_repo import GoogleSheetsRepository
except ImportError as e:
    st.error(f"⚠️ Kritik Hata: Dosyalar bulunamadı! ({e})")
    st.stop()

load_dotenv()


def main():
    st.title("🤖 AIESEC OGT Operasyon Paneli v2.1")

    # --- SESSION STATE ---
    if 'applicants' not in st.session_state: st.session_state['applicants'] = []
    if 'project_offset' not in st.session_state: st.session_state.project_offset = 0
    if 'filtered_projects_cache' not in st.session_state: st.session_state.filtered_projects_cache = []
    if 'ai_results_cache' not in st.session_state: st.session_state.ai_results_cache = {}

    # --- YAN MENÜ ---
    st.sidebar.header("⚙️ Veri Kaynakları")
    if st.sidebar.button("🧹 Sıfırla"):
        st.session_state.clear()
        st.rerun()

    # BURASI GÜNCELLENDİ: Yeni App ID ve View ID Geri Geldi
    app_id = st.sidebar.text_input("Podio App ID", value="23409870")
    view_id = st.sidebar.text_input("View ID (Örn: Sign Up Listesi)",value="61478954",
                                    help="Podio'da filtrelediğin listenin URL'sindeki son sayıdır.")

    if st.sidebar.button("📦 Adayları Çek"):
        with st.spinner("Podio'ya bağlanılıyor..."):
            try:
                repo = PodioRepository()
                # View ID varsa onu kullan, yoksa boş gönder
                v_id = view_id if view_id.strip() else None
                apps = repo.fetch_applicants(app_id, view_id=v_id)
                st.session_state['applicants'] = apps
                st.sidebar.success(f"✅ {len(apps)} aday yüklendi!")
            except Exception as e:
                st.sidebar.error(f"Hata: {e}")

    st.sidebar.divider()

    # --- YENİ FİLTRELER ---
    st.sidebar.header("🎯 Gelişmiş Filtreler")
    f_country = st.sidebar.text_input("🌍 Ülke (Örn: India)")
    f_field = st.sidebar.text_input("💼 Departman (Örn: Marketing)")
    f_duration = st.sidebar.selectbox("⏳ Süre", ["Farketmez", "Kısa (Short)", "Orta (Medium)", "Uzun (Long)"])
    f_paid_only = st.sidebar.checkbox("💰 Sadece Maaşlı Projeler")

    # --- ANA EKRAN ---
    if st.session_state['applicants']:
        names = [a.full_name for a in st.session_state['applicants']]
        selected_name = st.selectbox("Aday Seç:", names)
        if 'last_selected_candidate' not in st.session_state:
            st.session_state.last_selected_candidate = selected_name

        if st.session_state.last_selected_candidate != selected_name:
            # Aday değiştiği an hafızayı ve ekranı temizle
            st.session_state.ai_results_cache = {}
            st.session_state.filtered_projects_cache = []
            st.session_state.project_offset = 0
            st.session_state.last_selected_candidate = selected_name
            st.rerun()  # Sayfayı yenile
        ep = next((a for a in st.session_state['applicants'] if a.full_name == selected_name), None)

        if ep:
            # Aday Kartı
            c1, c2 = st.columns(2)
            c1.info(f"👤 **{ep.full_name}**")
            c2.warning(f"🎓 {ep.background or 'Bölüm Yok'}\n\n📧 {ep.email}")

            # CV Yükleme
            uploaded_file = st.file_uploader("📄 CV Yükle (PDF)", type="pdf")
            cv_text = ""
            if uploaded_file:
                try:
                    pdf = PyPDF2.PdfReader(uploaded_file)
                    for p in pdf.pages: cv_text += p.extract_text()
                    st.caption("✅ CV okundu.")
                except:
                    st.error("PDF Hatası")

            st.divider()

            # Butonlar
            col_b1, col_b2 = st.columns(2)
            btn_start = col_b1.button("🚀 Eşleşmeleri Bul")
            btn_more = col_b2.button("🔄 Sonraki 3 Proje")

            # Servisler
            matcher = AIMatcher()
            expa = ExpaRepository()
            scraper = JDScraper()

            # 1. FİLTRELEME & SIRALAMA
            if btn_start:
                st.session_state.project_offset = 0
                st.session_state.ai_results_cache = {}
                with st.spinner("🧠 CV'den yetenekler ayrıştırılıyor..."):
                    try:
                        # Eğer CV metni varsa AI'dan saf yetenekleri iste
                        if cv_text:
                            ai_keywords = matcher.extract_keywords_from_cv(cv_text)
                            st.caption(f"🎯 AI'nın Bulduğu Yetenekler: {', '.join(ai_keywords)}")
                        else:
                            # CV yoksa Podio verilerini kullan
                            ai_keywords = (ep.background + " " + " ".join(ep.skills)).lower().split()
                    except Exception as e:
                        st.error(f"AI Keyword Hatası: {e}")
                        ai_keywords = []

                with st.spinner("EXPA'dan projeler taranıyor..."):
                    try:
                        all_projects = expa.fetch_data()

                        # Filtreleme (Ülke & Departman)
                        filtered = []
                        for p in all_projects:
                            search_text = (p.title + " " + p.organisation + " " + getattr(p, 'home_lc', '')).lower()
                            if f_country and f_country.lower() not in search_text: continue
                            if f_field and f_field.lower() not in search_text: continue
                            filtered.append(p)

                        if not filtered:
                            st.error("❌ Kriterlere uygun proje bulunamadı.")
                            st.session_state.filtered_projects_cache = []
                        else:
                            # --- AI DESTEKLİ PUANLAMA ---
                            scored_projects = []

                            # Artık AI'dan gelen temiz kelimeleri kullanıyoruz
                            keywords = ai_keywords
                            synonyms = {
                                "marketing": ["sales", "brand", "market", "digital"],
                                "teaching": ["education", "teacher", "language", "school"],
                                "business": ["management", "admin", "finance", "operations"],
                                "software": ["developer", "coding", "engineer", "it", "tech"]
                            }

                            expanded_keywords = list(keywords)  # Kopyasını al
                            for k in keywords:
                                for main_key, sub_list in synonyms.items():
                                    if k in sub_list or k == main_key:
                                        expanded_keywords.extend(sub_list)

                            keywords = list(set(expanded_keywords))  # Tekrarları sil

                            for p in filtered:
                                score = 0
                                title_txt = p.title.lower()
                                org_txt = p.organisation.lower()
                                # EXPA'dan gelen 'backgrounds' ve 'skills' listelerini de string yap
                                tags_txt = " ".join(p.backgrounds + p.skills).lower()

                                for k in keywords:
                                    # Anahtar kelime Başlıkta geçiyorsa: 30 Puan (Çok önemli)
                                    if k in title_txt:
                                        score += 30

                                    # Projenin etiketlerinde (tags) geçiyorsa: 20 Puan
                                    elif k in tags_txt:
                                        score += 20

                                    # Kurum adında geçiyorsa: 10 Puan
                                    elif k in org_txt:
                                        score += 10

                                # Rastgelelik (Çeşitlilik için)
                                score += random.randint(0, 5)

                                if score > 0:  # Sadece puan alanları ekle
                                    scored_projects.append((score, p))

                            scored_projects.sort(key=lambda x: x[0], reverse=True)
                            st.session_state.filtered_projects_cache = [x[1] for x in scored_projects]

                            top_score = scored_projects[0][0] if scored_projects else 0
                            st.success(f"🔍 {len(filtered)} proje tarandı. En yüksek eşleşme skoru: {top_score}")

                    except Exception as e:
                        st.error(f"Filtreleme Hatası: {e}")

            # 2. SAYFALAMA
            if btn_more:
                if st.session_state.filtered_projects_cache:
                    st.session_state.project_offset += 3
                    if st.session_state.project_offset >= len(st.session_state.filtered_projects_cache):
                        st.warning("⚠️ Liste başa döndü.")
                        st.session_state.project_offset = 0

            # 3. ANALİZ VE GÖSTERİM
            cache = st.session_state.filtered_projects_cache
            offset = st.session_state.project_offset

            if cache:
                batch = cache[offset: offset + 3]

                if batch:
                    st.info(f"📋 Analiz Ediliyor: {offset + 1} - {offset + len(batch)}")
                    batch_key = f"batch_{offset}"

                    if batch_key not in st.session_state.ai_results_cache:
                        with st.spinner("🌍 Proje detayları web'den çekiliyor ve AI analiz ediyor..."):
                            for p in batch:
                                if len(p.description) < 200 and p.link:
                                    try:
                                        full_desc = scraper.fetch_description(p.link)
                                        p.description = full_desc
                                    except:
                                        pass

                            results = matcher.generate_batch_report(ep, batch, cv_text)
                            st.session_state.ai_results_cache[batch_key] = results
                    else:
                        results = st.session_state.ai_results_cache[batch_key]

                    # Sonuçları Bas
                    if results:
                        for i, res in enumerate(results):
                            try:
                                p_idx = res.get('project_index', i)
                                p = batch[p_idx] if p_idx < len(batch) else batch[i]

                                with st.expander(f"📌 {p.title} - {p.organisation} (Skor: {res.get('score', 0)})",
                                                 expanded=True):
                                    t1, t2 = st.tabs(["🧠 Analiz", "💬 Aksiyon"])

                                    with t1:
                                        st.markdown(f"**💡 Satış:** {res.get('sales_pitch')}")
                                        st.markdown(f"**⚠️ Riskler:** {res.get('pain_points')}")

                                        with st.popover("📄 İş Tanımı Detayı"):
                                            st.write(p.description)

                                    with t2:
                                        # WhatsApp
                                        msg = res.get('whatsapp_msg', '')
                                        st.text_area("Mesaj Taslağı:", value=msg, height=100)
                                        encoded_msg = urllib.parse.quote(msg)
                                        phone_num = getattr(ep, 'phone', '').replace(" ", "").replace("+", "")
                                        st.link_button("📱 WhatsApp", f"https://wa.me/{phone_num}?text={encoded_msg}")

                                        # Podio + Sheets Butonu
                                        st.divider()
                                        if st.button(f"📝 Podio & Tabloya Kaydet", key=f"btn_podio_{i}"):
                                            with st.spinner("İşleniyor..."):
                                                # 1. Podio Yorum (Aktif)
                                                try:
                                                    comment_body = f"""
                                                    [AI ANALİZİ - {p.title}]
                                                    ✅ Uyum Skoru: {res.get('score')}/100
                                                    💡 Strateji: {res.get('sales_pitch')}
                                                    🔗 Link: https://aiesec.org/opportunity/{p.op_id}
                                                    """
                                                    repo_podio = PodioRepository()
                                                    repo_podio.add_comment(ep.ep_id, comment_body)
                                                    st.toast("✅ Podio yorumu eklendi!")
                                                except Exception as e:
                                                    st.error(f"Podio Hatası: {e}")

                                                # 2. Google Sheets (Aktif)
                                                try:
                                                    sheets = GoogleSheetsRepository()
                                                    sheets.log_match(
                                                        "OGT_Analiz_Loglari",
                                                        ep.full_name, p.title, p.organisation, p.country,
                                                        res.get('score'), res.get('sales_pitch')
                                                    )
                                                    st.toast("✅ Tabloya işlendi!")
                                                except Exception as e:
                                                    st.error(f"Sheet Hatası: {e}")

                            except Exception as e:
                                st.error(f"Gösterim Hatası: {e}")

                        # CSV İndirme
                        st.divider()
                        st.subheader("💾 Raporlama")
                        report_data = []
                        for res in results:
                            p_idx = res.get('project_index', 0)
                            p_obj = batch[p_idx] if p_idx < len(batch) else batch[0]
                            report_data.append({
                                "Aday": ep.full_name,
                                "Proje": p_obj.title,
                                "Skor": res.get('score'),
                                "Strateji": res.get('sales_pitch')
                            })
                        if report_data:
                            df = pd.DataFrame(report_data)
                            csv = df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button("📥 İndir (CSV)", data=csv, file_name="analiz.csv", mime="text/csv")

    else:
        st.info("👈 Podio ID ve View ID (Opsiyonel) girip 'Adayları Çek' butonuna basın.")


if __name__ == "__main__":
    main()