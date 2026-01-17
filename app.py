import streamlit as st
import sys
import os
import urllib.parse
import PyPDF2
import pandas as pd
import random
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util

from src.services.pdf_generator import PDFReportGenerator
# --- STREAMLIT SECRETS KÖPRÜSÜ ---
# Bu kod, Streamlit kasasındaki şifreleri uygulamanın kullanabileceği hale getirir.
if hasattr(st, "secrets"):
    # 1. Tüm şifreleri sisteme tanıt
    for key, value in st.secrets.items():
        os.environ[key] = str(value)
    
    # 2. Google Dosyasını (credentials.json) sanal olarak oluştur
    if "GOOGLE_CREDENTIALS" in st.secrets:
        with open("credentials.json", "w") as f:
            f.write(st.secrets["GOOGLE_CREDENTIALS"])
# ----------------------------------

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

# --- YAPAY ZEKA MODELİNİ YÜKLE (ÖNBELLEK) ---
@st.cache_resource
def load_embedding_model():
    # Bu model hem hızlı hem de anlamsal ilişkileri çok iyi yakalar
    return SentenceTransformer('all-MiniLM-L6-v2')
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
                            country_check = (p.country or "").lower()
                            if "turkey" in country_check or "türkiye" in country_check:
                                continue  # Bu projeyi atla, listeye ekleme
                            search_text = (p.title + " " + p.organisation + " " + getattr(p, 'home_lc', '')).lower()
                            if f_country and f_country.lower() not in search_text: continue
                            if f_field and f_field.lower() not in search_text: continue
                            filtered.append(p)

                        if not filtered:
                            st.error("❌ Kriterlere uygun proje bulunamadı.")
                            st.session_state.filtered_projects_cache = []
                        else:
                            # --- 1. MODELİ HAZIRLA ---
                            embedder = load_embedding_model()  # Modeli çağır

                            # --- 2. VEKTÖR HESAPLAMA (SEMANTİK ARAMA) ---
                            st.info("🧠 Yapay Zeka, ilanları anlamsal olarak analiz ediyor...")

                            # Adayın profilini metne çevir
                            candidate_text = f"{ep.background} {' '.join(ep.skills)}"
                            # Vektör oluştur
                            candidate_embedding = embedder.encode(candidate_text, convert_to_tensor=True)

                            # Tüm projelerin başlık ve açıklamalarını vektöre çevir (Toplu işlem)
                            project_texts = [f"{p.title} {p.organisation} {p.description[:300]}" for p in filtered]
                            project_embeddings = embedder.encode(project_texts, convert_to_tensor=True)

                            # Benzerlik skorlarını hesapla (Cosine Similarity)
                            # Sonuç 0 ile 1 arasındadır (0.85 = %85 Benzerlik)
                            cosine_scores = util.cos_sim(candidate_embedding, project_embeddings)[0]

                            # --- 3. HİBRİT PUANLAMA (Vektör + Kelime) ---
                            scored_projects = []

                            # Destekleyici anahtar kelimeler (Bonus puan için)
                            keywords = (ep.background + " " + " ".join(ep.skills)).lower().split()

                            for i, p in enumerate(filtered):
                                final_score = 0

                                # A. Vektör Puanı (Baz Puan)
                                # 0.1 - 1.0 arasındaki sayıyı 100'lük sisteme çeviriyoruz.
                                vector_score = float(cosine_scores[i]) * 100
                                final_score += vector_score

                                # B. Kelime Bonusu (Eski Yöntem Destekli)
                                p_txt = (p.title + " " + p.organisation).lower()
                                for k in keywords:
                                    if len(k) > 3 and k in p_txt:
                                        final_score += 5  # Kelime geçiyorsa ekstra 5 puan

                                # C. Rastgelelik (Çeşitlilik)
                                final_score += random.randint(0, 3)

                                # Eşik Değer (Çok alakasızları elemek için örn: 20 puan altı)
                                if final_score > 20:
                                    scored_projects.append((final_score, p))

                            # Puanı yüksekten düşüğe sırala
                            scored_projects.sort(key=lambda x: x[0], reverse=True)

                            # Listeyi güncelle
                            st.session_state.filtered_projects_cache = [x[1] for x in scored_projects]

                            # Kullanıcıya bilgi ver
                            top_score = round(scored_projects[0][0], 1) if scored_projects else 0
                            st.success(f"🚀 {len(filtered)} proje Yapay Zeka ile tarandı! En yüksek uyum: {top_score}")
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
                                        st.markdown("### 🧐 Teknik Uygunluk Analizi")
                                        st.info(res.get('suitability_analysis', 'Analiz yapılamadı.'))

                                        # --- 2. SATIŞ TAKTİKLERİ ---
                                        st.markdown("### 🎯 Satış Stratejisi")
                                        st.success(f"**Nasıl Sunmalısın:** {res.get('sales_pitch', '')}")

                                        st.markdown("### 🥊 İkna Kozları (Pain Points)")
                                        st.warning(res.get('pain_points', ''))
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

                                        st.divider()
                                        # --- PDF RAPOR BUTONU ---
                                        if st.button("📄 PDF Raporu İndir", key=f"btn_pdf_{i}"):
                                            pdf_gen = PDFReportGenerator()
                                            pdf_file = pdf_gen.create_report(ep.full_name, p, res)

                                            with open(pdf_file, "rb") as f:
                                                st.download_button(
                                                    label="📥 Dosyayı Bilgisayarına İndir",
                                                    data=f,
                                                    file_name=pdf_file,
                                                    mime="application/pdf"
                                                )

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
