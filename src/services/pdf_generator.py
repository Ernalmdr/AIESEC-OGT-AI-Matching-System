from fpdf import FPDF
import os


class PDFReportGenerator(FPDF):
    def header(self):
        # AIESEC Logosu (Varsa ekler, yoksa hata vermez)
        # self.image('logo.png', 10, 8, 33)
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'AIESEC OGT - Aday Eşleştirme Raporu', align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', align='C')

    def create_report(self, candidate_name, project, ai_result):
        self.add_page()

        # Türkçe karakter sorunu olmaması için standart font yerine
        # Unicode destekli bir font eklemek gerekir ama
        # Şimdilik basit olması için Latin karakterlere zorlayacağız
        # Veya 'Helvetica' kullanıp Türkçe karakterleri temizleyeceğiz.

        self.set_font("Helvetica", size=12)

        # 1. Başlık Alanı
        self.set_font("Helvetica", 'B', 14)
        self.cell(0, 10, f"Aday: {self.clean_text(candidate_name)}", ln=True)
        self.ln(5)

        # 2. Proje Bilgileri Kutu
        self.set_fill_color(240, 240, 240)  # Gri Arkaplan
        self.rect(10, self.get_y(), 190, 40, 'F')

        self.set_font("Helvetica", 'B', 12)
        self.cell(0, 8, f"Onerilen Proje: {self.clean_text(project.title)}", ln=True)
        self.set_font("Helvetica", '', 11)
        self.cell(0, 8, f"Sirket: {self.clean_text(project.organisation)}", ln=True)
        self.cell(0, 8, f"Lokasyon: {self.clean_text(project.country)}", ln=True)
        self.cell(0, 8, f"Maas: {self.clean_text(project.salary)}", ln=True)
        self.ln(15)

        # 3. Yapay Zeka Analizi
        self.set_font("Helvetica", 'B', 12)
        self.set_text_color(0, 51, 102)  # Lacivert
        self.cell(0, 10, "Yapay Zeka Strateji Analizi", ln=True)
        self.set_text_color(0, 0, 0)  # Siyah

        self.set_font("Helvetica", '', 11)
        self.multi_cell(0, 8, f"Strateji: {self.clean_text(ai_result.get('sales_pitch', ''))}")
        self.ln(5)

        self.set_text_color(200, 0, 0)  # Kırmızı
        self.multi_cell(0, 8, f"Riskler & Onlemler: {self.clean_text(ai_result.get('pain_points', ''))}")
        self.set_text_color(0, 0, 0)

        # 4. İletişim & Link
        self.ln(10)
        self.set_font("Helvetica", 'B', 10)
        self.cell(0, 10, "Basvuru Linki:", ln=True)
        self.set_font("Helvetica", 'U', 10)
        self.set_text_color(0, 0, 255)
        self.cell(0, 5, project.link, link=project.link, ln=True)

        # Kaydet
        filename = f"Rapor_{candidate_name.replace(' ', '_')}.pdf"
        self.output(filename)
        return filename

    def clean_text(self, text):
        """Türkçe karakterleri İngilizce'ye çevirir (Basit çözüm)"""
        if not text: return ""
        mapping = {
            'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ı': 'i', 'İ': 'I',
            'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S', 'ç': 'c', 'Ç': 'C'
        }
        for k, v in mapping.items():
            text = text.replace(k, v)
        return text.encode('latin-1', 'replace').decode('latin-1')