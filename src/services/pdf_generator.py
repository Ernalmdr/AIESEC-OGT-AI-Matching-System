from fpdf import FPDF
import os

class PDFReportGenerator(FPDF):
    def clean_text(self, text):
        """
        Türkçe karakterleri İngilizce karşılıklarına çevirir ve 
        PDF'in desteklemediği karakterleri temizler.
        """
        if not text: return ""
        text = str(text) # Sayı gelirse yazıya çevir
        
        mapping = {
            'ü': 'u', 'Ü': 'U',
            'ö': 'o', 'Ö': 'O',
            'ı': 'i', 'İ': 'I',
            'ğ': 'g', 'Ğ': 'G',
            'ş': 's', 'Ş': 'S',
            'ç': 'c', 'Ç': 'C',
            'â': 'a', 'î': 'i', 'û': 'u' # Şapkalı harfler
        }
        for k, v in mapping.items():
            text = text.replace(k, v)
            
        # Latin-1 dışında kalan her şeyi '?' yapar, hata vermesini engeller
        return text.encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        # Header kısmındaki Türkçe karakterleri de temizliyoruz!
        title = self.clean_text('AIESEC OGT - Aday Eslestirme Raporu')
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, title, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        page_txt = self.clean_text(f'Sayfa {self.page_no()}')
        self.cell(0, 10, page_txt, align='C')

    def create_report(self, candidate_name, project, ai_result):
        self.add_page()
        self.set_font("Helvetica", size=12)
        
        # --- 1. Başlık Alanı ---
        self.set_font("Helvetica", 'B', 14)
        c_name = self.clean_text(f"Aday: {candidate_name}")
        self.cell(0, 10, c_name, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        
        # --- 2. Proje Bilgileri Kutu ---
        # Gri Arkaplan
        self.set_fill_color(240, 240, 240) 
        # Rect(x, y, w, h, style)
        self.rect(10, self.get_y(), 190, 45, 'F')
        
        self.set_font("Helvetica", 'B', 12)
        # Türkçe karakterleri temizleyerek yaz
        p_title = self.clean_text(f"Onerilen Proje: {project.title}")
        self.cell(0, 8, p_title, new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", '', 11)
        p_org = self.clean_text(f"Sirket: {project.organisation}")
        self.cell(0, 8, p_org, new_x="LMARGIN", new_y="NEXT")
        
        p_country = self.clean_text(f"Lokasyon: {project.country}")
        self.cell(0, 8, p_country, new_x="LMARGIN", new_y="NEXT")
        
        p_salary = self.clean_text(f"Maas: {project.salary}")
        self.cell(0, 8, p_salary, new_x="LMARGIN", new_y="NEXT")
        
        self.ln(15)
        
        # --- 3. Yapay Zeka Analizi ---
        self.set_font("Helvetica", 'B', 12)
        self.set_text_color(0, 51, 102) # Lacivert
        self.cell(0, 10, self.clean_text("Yapay Zeka Strateji Analizi"), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0) # Siyah
        
        self.set_font("Helvetica", '', 11)
        # Multi cell satır atlamalı metinler içindir
        strategy_txt = self.clean_text(f"Strateji: {ai_result.get('sales_pitch', '')}")
        self.multi_cell(0, 8, strategy_txt)
        self.ln(5)
        
        self.set_text_color(200, 0, 0) # Kırmızı
        risk_txt = self.clean_text(f"Riskler & Onlemler: {ai_result.get('pain_points', '')}")
        self.multi_cell(0, 8, risk_txt)
        self.set_text_color(0, 0, 0)
        
        # --- 4. İletişim & Link ---
        self.ln(10)
        self.set_font("Helvetica", 'B', 10)
        self.cell(0, 10, self.clean_text("Basvuru Linki:"), new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", 'U', 10)
        self.set_text_color(0, 0, 255)
        # Link kısmında temizlemeye gerek yok ama URL'de özel karakter varsa bozulabilir
        # Link metni temiz, linkin kendisi orjinal kalsın
        link_url = project.link
        self.cell(0, 5, self.clean_text(link_url), link=link_url, new_x="LMARGIN", new_y="NEXT")
        
        # Dosyayı kaydet
        # Dosya adındaki boşlukları ve Türkçe karakterleri de temizleyelim
        safe_name = self.clean_text(candidate_name).replace(" ", "_")
        filename = f"Rapor_{safe_name}.pdf"
        
        self.output(filename)
        return filename
