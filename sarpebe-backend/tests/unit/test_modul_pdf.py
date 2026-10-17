import pytest

from app.schemas.lesson_plan_content import GeneratedModul, Identity, ModulContent, Reference
from app.utils.modul_pdf import generate_modul_pdf, reference_line
from app.utils.pdf_extract import extract_pdf
from tests.factories import make_modul_dict


def make_content(meetings: int = 2, **overrides) -> ModulContent:
    generated = GeneratedModul.model_validate(make_modul_dict(meetings=meetings, **overrides))
    return ModulContent(
        **generated.model_dump(),
        identity=Identity(
            subject="IPS", grade_level="9", fase="D", topic="Pelaku dan kegiatan ekonomi",
            meetings=meetings, minutes_per_meeting=80, teaching_model="diskusi_kelompok",
        ),
        references=[Reference(id="S1", document_title="CP IPS.pdf", page=14, page_end=15, heading="Elemen Pemahaman")],
    )


def read(pdf_bytes: bytes):
    result = extract_pdf(pdf_bytes)
    text = "\n".join(b.text for page in result.pages for b in page.blocks if b.kind == "text")
    tables = [b.text for page in result.pages for b in page.blocks if b.kind == "table"]
    return result, text, tables


def test_the_pdf_is_a_valid_document():
    pdf = generate_modul_pdf(make_content())
    assert pdf.startswith(b"%PDF")
    assert extract_pdf(pdf).has_text


def test_identity_title_and_every_component_are_present():
    _, prose, tables = read(generate_modul_pdf(make_content()))
    text = prose + "\n" + "\n".join(tables)  # the identity block is itself a (headless) table
    for expected in (
        "MODUL AJAR KURIKULUM MERDEKA",
        "Pelaku dan Kegiatan Ekonomi di Sekitar Kita",
        "Kelas 9 (Fase D)",
        "2 pertemuan x 80 menit (160 menit)",
        "A. INFORMASI UMUM",
        "B. KOMPONEN INTI",
        "C. LAMPIRAN",
        "Tujuan pembelajaran",
        "Pertemuan 1",
        "Pertemuan 2",
        "Asesmen diagnostik",
        "Pengayaan",
        "Remedial",
        "LKPD: Peta alur barang",
        "Bahan bacaan peserta didik",
    ):
        assert expected in text, expected


def test_meeting_activities_and_assessment_are_real_tables():
    _, _, tables = read(generate_modul_pdf(make_content()))
    joined = "\n".join(tables)

    activity_tables = [t for t in tables if t.splitlines()[0] == "| Tahap | Waktu (menit) | Kegiatan | Metode |"]
    assert len(activity_tables) == 2  # one per meeting
    assert "| Pendahuluan | 15 |" in activity_tables[0]
    assert any(t.splitlines()[0].startswith("| Kriteria | 4 (Sangat baik)") for t in tables)  # rubric
    assert any(t.splitlines()[0].startswith("| Jenis | Teknik | Instrumen | Waktu") for t in tables)  # overview
    assert "| Dimensi | Wujud dalam kegiatan |" in joined
    assert "| Istilah | Pengertian |" in joined


def test_cited_objectives_show_their_source_marker_and_references_are_listed():
    _, text, _ = read(generate_modul_pdf(make_content()))
    assert "menganalisis interaksi antarpelaku ekonomi. [S1]" in text.replace("\n", " ") or "[S1]" in text
    assert "[S1] CP IPS.pdf, hlm. 14-15, Elemen Pemahaman" in text


def test_typographic_punctuation_is_rendered_not_rejected():
    content = make_content()
    content.title = "Ekonomi – “Pelaku” dan ‘Kegiatan’ … ≥ 80%"
    content.meetings[0].activities.rows[0][2] = "Guru bertanya: “Apa yang kamu beli hari ini?” – lalu mencatat."

    _, text, tables = read(generate_modul_pdf(content))

    assert "Ekonomi – “Pelaku”" in text
    assert any("“Apa yang kamu beli hari ini?”" in t for t in tables)


def test_a_long_module_spans_pages_with_numbered_footers():
    content = make_content(meetings=6)
    content.attachments.reading_material = "\n".join(f"Paragraf bacaan nomor {i} membahas kegiatan ekonomi sehari-hari." for i in range(80))

    result, text, _ = read(generate_modul_pdf(content))

    assert len(result.pages) >= 3
    assert "Halaman 1/" in text and f"Halaman {len(result.pages)}/{len(result.pages)}" in text


def test_table_headings_repeat_on_every_page_a_table_spans():
    content = make_content(meetings=1)
    content.assessment.rubric.rows = [[f"Kriteria nomor {i}", "a", "b", "c", "d"] for i in range(70)]

    result, _, tables = read(generate_modul_pdf(content))

    rubric_parts = [t for t in tables if t.splitlines()[0].startswith("| Kriteria | 4 (Sangat baik)")]
    assert len(result.pages) >= 2
    assert len(rubric_parts) >= 2  # split across pages, heading row repeated on each


def test_optional_sections_may_be_empty():
    content = make_content()
    content.initial_competencies = []
    content.pancasila_profile = []
    content.facilities = []
    content.enrichment = []
    content.remedial = []
    content.reflection.teacher = []
    content.reflection.students = []
    content.attachments.glossary = []
    content.attachments.reading_material = ""
    content.references = []

    _, text, _ = read(generate_modul_pdf(content))

    assert "Pertemuan 1" in text
    assert "Pengayaan" not in text and "Glosarium" not in text and "Sumber rujukan" not in text


@pytest.mark.parametrize("page,page_end,expected", [
    (14, 14, "hlm. 14"),
    (14, 16, "hlm. 14-16"),
    (None, None, "halaman tidak tercatat"),
])
def test_reference_lines_describe_the_page_range(page, page_end, expected):
    line = reference_line(Reference(id="S2", document_title="ATP.pdf", page=page, page_end=page_end, heading=None))
    assert line == f"[S2] ATP.pdf, {expected}"
