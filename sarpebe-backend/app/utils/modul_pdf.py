"""
PDF export for a Modul Ajar in schema version 2: identity, every component, real tables (header row
repeats across pages) and the reference list. The original simple format is rendered by
pdf_generator.generate_lesson_plan_pdf.
"""
from io import BytesIO
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

from app.schemas.lesson_plan_content import ModulContent, Reference, Table

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_FAMILY = "DejaVu"  # bundled: the core Helvetica font cannot encode the dashes and quotes models write
TABLE_HEADER_STYLE = FontFace(emphasis="BOLD", fill_color=(232, 238, 252))
ACTIVITY_COLUMN_WIDTHS = (0.16, 0.12, 0.52, 0.20)


class ModulPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        self.add_font(FONT_FAMILY, "", str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font(FONT_FAMILY, "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        self.add_font(FONT_FAMILY, "I", str(FONT_DIR / "DejaVuSans-Oblique.ttf"))
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 16, 18)
        self.alias_nb_pages()

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font(FONT_FAMILY, "I", 8)
        self.cell(self.epw, 8, f"Halaman {self.page_no()}/{{nb}}", align="C")


def _write_title(pdf: ModulPDF, text: str) -> None:
    pdf.set_font(FONT_FAMILY, "B", 16)
    pdf.multi_cell(pdf.epw, 8, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _write_part(pdf: ModulPDF, text: str) -> None:
    """A major part, e.g. 'B. KOMPONEN INTI', with a rule under it."""
    pdf.ln(4)
    pdf.set_font(FONT_FAMILY, "B", 12)
    pdf.cell(pdf.epw, 8, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(160, 170, 195)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
    pdf.ln(3)


def _write_heading(pdf: ModulPDF, text: str) -> None:
    pdf.ln(2)
    pdf.set_font(FONT_FAMILY, "B", 10.5)
    pdf.multi_cell(pdf.epw, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _write_label(pdf: ModulPDF, text: str) -> None:
    pdf.set_font(FONT_FAMILY, "B", 10)
    pdf.cell(pdf.epw, 6, text, new_x="LMARGIN", new_y="NEXT")


def _write_paragraph(pdf: ModulPDF, text: str) -> None:
    if not text.strip():
        return
    pdf.set_font(FONT_FAMILY, "", 10)
    pdf.multi_cell(pdf.epw, 5.5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def _write_list(pdf: ModulPDF, items: list[str], *, numbered: bool = False, suffixes: list[str] | None = None) -> None:
    pdf.set_font(FONT_FAMILY, "", 10)
    indent = 6
    for position, item in enumerate(items, start=1):
        if not item.strip():
            continue
        marker = f"{position}." if numbered else "•"
        suffix = f" {suffixes[position - 1]}" if suffixes and suffixes[position - 1] else ""
        pdf.set_x(pdf.l_margin)
        pdf.cell(indent, 5.5, marker)
        pdf.multi_cell(pdf.epw - indent, 5.5, item + suffix, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def _write_table(
    pdf: ModulPDF,
    columns: list[str],
    rows: list[list[str]],
    *,
    caption: str = "",
    col_widths: tuple[float, ...] | None = None,
) -> None:
    if caption.strip():
        pdf.set_font(FONT_FAMILY, "I", 9)
        pdf.multi_cell(pdf.epw, 5, caption, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.set_font(FONT_FAMILY, "", 9)
    with pdf.table(
        col_widths=col_widths,
        text_align="LEFT",
        v_align="TOP",
        headings_style=TABLE_HEADER_STYLE,
        padding=1.8,
        line_height=5,
        repeat_headings=1,
    ) as table:
        header = table.row()
        for column in columns:
            header.cell(column)
        for cells in rows:
            row = table.row()
            for cell in cells:
                row.cell(cell)
    pdf.ln(3)


def _write_model_table(pdf: ModulPDF, table: Table, col_widths: tuple[float, ...] | None = None) -> None:
    _write_table(pdf, table.columns, table.rows, caption=table.caption, col_widths=col_widths)


def reference_line(reference: Reference) -> str:
    pages = f"hlm. {reference.page}" if reference.page is not None else "halaman tidak tercatat"
    if reference.page is not None and reference.page_end and reference.page_end != reference.page:
        pages = f"hlm. {reference.page}-{reference.page_end}"
    section = f", {reference.heading}" if reference.heading else ""
    return f"[{reference.id}] {reference.document_title}, {pages}{section}"


def generate_modul_pdf(content: ModulContent) -> bytes:
    """Renders a schema-version-2 Modul Ajar."""
    pdf = ModulPDF()
    pdf.add_page()

    identity = content.identity
    fase = f" (Fase {identity.fase})" if identity.fase else ""
    total_minutes = identity.meetings * identity.minutes_per_meeting

    pdf.set_font(FONT_FAMILY, "B", 11)
    pdf.cell(pdf.epw, 7, "MODUL AJAR KURIKULUM MERDEKA", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    _write_title(pdf, content.title.strip() or identity.topic)

    pdf.set_font(FONT_FAMILY, "", 10)
    with pdf.table(
        col_widths=(0.28, 0.72),
        text_align="LEFT",
        v_align="TOP",
        first_row_as_headings=False,
        padding=1.8,
        line_height=5.5,
    ) as info:
        for label, value in (
            ("Mata pelajaran", identity.subject),
            ("Kelas / Fase", f"Kelas {identity.grade_level}{fase}"),
            ("Topik", identity.topic),
            (
                "Alokasi waktu",
                f"{identity.meetings} pertemuan x {identity.minutes_per_meeting} menit ({total_minutes} menit)",
            ),
            ("Model pembelajaran", content.learning_model.name),
        ):
            row = info.row()
            row.cell(label, style=FontFace(emphasis="BOLD"))
            row.cell(value)

    # A. Informasi umum
    _write_part(pdf, "A. INFORMASI UMUM")
    if content.initial_competencies:
        _write_heading(pdf, "Kompetensi awal")
        _write_list(pdf, content.initial_competencies)
    if content.pancasila_profile:
        _write_heading(pdf, "Profil Pelajar Pancasila")
        _write_table(
            pdf,
            ["Dimensi", "Wujud dalam kegiatan"],
            [[item.dimension, item.how] for item in content.pancasila_profile],
            col_widths=(0.3, 0.7),
        )
    if content.facilities:
        _write_heading(pdf, "Sarana dan prasarana")
        _write_list(pdf, content.facilities)
    if content.target_students.strip():
        _write_heading(pdf, "Target peserta didik")
        _write_paragraph(pdf, content.target_students)
    _write_heading(pdf, "Model pembelajaran")
    _write_paragraph(pdf, f"{content.learning_model.name}. {content.learning_model.rationale}")

    # B. Komponen inti
    _write_part(pdf, "B. KOMPONEN INTI")
    _write_heading(pdf, "Tujuan pembelajaran")
    _write_list(
        pdf,
        [objective.text for objective in content.learning_objectives],
        numbered=True,
        suffixes=[" ".join(f"[{source}]" for source in objective.source_ids) for objective in content.learning_objectives],
    )
    if content.meaningful_understanding:
        _write_heading(pdf, "Pemahaman bermakna")
        _write_list(pdf, content.meaningful_understanding)
    if content.trigger_questions:
        _write_heading(pdf, "Pertanyaan pemantik")
        _write_list(pdf, content.trigger_questions)
    if content.preparation:
        _write_heading(pdf, "Persiapan pembelajaran")
        _write_list(pdf, content.preparation)

    _write_heading(pdf, "Kegiatan pembelajaran")
    for meeting in content.meetings:
        _write_label(pdf, f"Pertemuan {meeting.number}: {meeting.title}")
        widths = ACTIVITY_COLUMN_WIDTHS if len(meeting.activities.columns) == len(ACTIVITY_COLUMN_WIDTHS) else None
        _write_model_table(pdf, meeting.activities, widths)

    _write_heading(pdf, "Asesmen")
    for label, item in (
        ("Asesmen diagnostik", content.assessment.diagnostic),
        ("Asesmen formatif", content.assessment.formative),
        ("Asesmen sumatif", content.assessment.summative),
    ):
        _write_label(pdf, label)
        _write_paragraph(pdf, f"Teknik: {item.technique}. Instrumen: {item.instrument}. {item.description}")
    _write_model_table(pdf, content.assessment.overview)
    _write_model_table(pdf, content.assessment.rubric)

    if content.enrichment:
        _write_heading(pdf, "Pengayaan")
        _write_list(pdf, content.enrichment)
    if content.remedial:
        _write_heading(pdf, "Remedial")
        _write_list(pdf, content.remedial)
    if content.reflection.teacher or content.reflection.students:
        _write_heading(pdf, "Refleksi")
        if content.reflection.teacher:
            _write_label(pdf, "Untuk guru")
            _write_list(pdf, content.reflection.teacher)
        if content.reflection.students:
            _write_label(pdf, "Untuk peserta didik")
            _write_list(pdf, content.reflection.students)

    # C. Lampiran
    _write_part(pdf, "C. LAMPIRAN")
    worksheet = content.attachments.worksheet
    _write_heading(pdf, f"LKPD: {worksheet.title}")
    _write_paragraph(pdf, worksheet.instructions)
    _write_list(pdf, worksheet.tasks, numbered=True)
    if content.attachments.reading_material.strip():
        _write_heading(pdf, "Bahan bacaan peserta didik")
        for paragraph in content.attachments.reading_material.split("\n"):
            _write_paragraph(pdf, paragraph)
    if content.attachments.glossary:
        _write_heading(pdf, "Glosarium")
        _write_table(
            pdf,
            ["Istilah", "Pengertian"],
            [[entry.term, entry.definition] for entry in content.attachments.glossary],
            col_widths=(0.3, 0.7),
        )

    if content.references:
        _write_heading(pdf, "Sumber rujukan")
        _write_list(pdf, [reference_line(reference) for reference in content.references])

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
