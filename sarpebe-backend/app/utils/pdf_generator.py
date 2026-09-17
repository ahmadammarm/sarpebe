from io import BytesIO
from fpdf import FPDF
from typing import Any

class LessonPlanPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "RENCANA PELAKSANAAN PEMBELAJARAN (RPP) / MODUL AJAR", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Halaman {self.page_no()}/{{nb}}", align="C")

def generate_lesson_plan_pdf(plan_metadata: dict[str, Any], content: dict[str, Any]) -> bytes:
    pdf = LessonPlanPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Metadata section
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 8, "Mata Pelajaran:", new_x="RIGHT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, str(plan_metadata.get("subject", "-")), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 8, "Fase / Kelas:", new_x="RIGHT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Kelas {plan_metadata.get('grade_level', '-')}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 8, "Topik / Materi:", new_x="RIGHT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, str(plan_metadata.get("topic", "-")), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Title
    title = content.get("title") or "Modul Ajar"
    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(0, 8, f"Judul: {title}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Helper function for sections
    def add_section(header: str, items: Any):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, header, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    duration = item.get("duration", "")
                    desc = item.get("description", "")
                    dur_prefix = f"({duration}) " if duration else ""
                    pdf.multi_cell(0, 6, f"- {dur_prefix}{desc}")
                else:
                    pdf.multi_cell(0, 6, f"- {str(item)}")
        elif isinstance(items, str):
            pdf.multi_cell(0, 6, items)
        pdf.ln(3)

    if content.get("objectives"):
        add_section("1. Tujuan Pembelajaran", content.get("objectives"))

    if content.get("materials"):
        add_section("2. Media & Sumber Belajar", content.get("materials"))

    if content.get("activities"):
        add_section("3. Kegiatan Pembelajaran", content.get("activities"))

    if content.get("assessment"):
        add_section("4. Penilaian / Asesmen", content.get("assessment"))

    if content.get("citations"):
        add_section("5. Referensi & Sitasi Dokumen Kurikulum", content.get("citations"))

    # Return bytes output
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
