from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Dokumen Kurikulum Merdeka - Simulasi', border=False, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'Capaian Pembelajaran Biologi Kelas 10', ln=True, align='L')
    pdf.ln(5)
    
    # Body text
    pdf.set_font('helvetica', '', 12)
    
    content = """
BAB 1: Struktur dan Fungsi Sel Hewan
Peserta didik diharapkan mampu memahami struktur dasar sel hewan, membedakan organel-organel sel (seperti nukleus, mitokondria, ribosom, membran sel, dan lisosom), serta mengidentifikasi fungsi masing-masing organel dalam menunjang kehidupan sel.

Metode Pembelajaran yang Disarankan:
- Observasi mikroskopik (mengamati sel epitel pipi).
- Diskusi kelompok interaktif mengenai analogi fungsi organel dengan pabrik/kota.
- Pembuatan model sel 3D menggunakan plastisin atau bahan daur ulang.

Penilaian Berbasis Proyek (Assessment):
Siswa mempresentasikan model sel 3D yang dibuat secara berkelompok dengan durasi maksimal 10 menit, mencakup penjelasan fungsi minimal 5 organel utama.

BAB 2: Ekosistem dan Jaring-jaring Makanan
Peserta didik dapat menganalisis interaksi antar komponen ekosistem, aliran energi, dan memprediksi dampak perubahan lingkungan terhadap jaring-jaring makanan.

Target Pemahaman (TP):
- Menggambarkan bagan rantai makanan dan jaring-jaring makanan.
- Memahami konsep produsen, konsumen tingkat 1-3, dan dekomposer.
"""
    
    # We use multi_cell to handle paragraph breaks and line wrapping
    pdf.multi_cell(0, 8, content)
    
    # Save the PDF
    output_path = os.path.join(os.getcwd(), "sample_kurikulum_biologi.pdf")
    pdf.output(output_path)
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    create_pdf()
