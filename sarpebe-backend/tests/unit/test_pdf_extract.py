from fpdf import FPDF

from app.utils.pdf_extract import extract_pdf, table_to_markdown


def build_pdf() -> bytes:
    """A one-page CP-like document: heading, paragraph, ruled table."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Elemen Pemahaman IPS", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 6,
        "Peserta didik memahami interaksi antarpelaku ekonomi dalam kegiatan produksi, distribusi, dan konsumsi.",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(6)
    with pdf.table() as table:
        header = table.row()
        header.cell("Elemen")
        header.cell("Capaian")
        first = table.row()
        first.cell("Pemahaman")
        first.cell("Menjelaskan konsep ekonomi")
        second = table.row()
        second.cell("Keterampilan")
        second.cell("Menyajikan data pasar")
    return bytes(pdf.output())


def blank_pdf(pages: int = 1) -> bytes:
    pdf = FPDF()
    for _ in range(pages):
        pdf.add_page()
    return bytes(pdf.output())


# --- table_to_markdown --------------------------------------------------------------------------

def test_table_to_markdown_renders_header_and_rows():
    markdown = table_to_markdown([["Elemen", "Capaian"], ["Pemahaman", "Menjelaskan"]])
    assert markdown == "| Elemen | Capaian |\n| --- | --- |\n| Pemahaman | Menjelaskan |"


def test_table_to_markdown_fills_merged_cells_from_the_row_above():
    markdown = table_to_markdown([["Elemen", "Capaian"], ["Pemahaman", "A"], [None, "B"]])
    assert "| Pemahaman | A |" in markdown
    assert "| Pemahaman | B |" in markdown


def test_table_to_markdown_escapes_pipes_and_flattens_newlines():
    markdown = table_to_markdown([["A", "B"], ["x | y", "baris satu\nbaris dua"]])
    assert "x \\| y" in markdown
    assert "baris satu baris dua" in markdown


def test_table_to_markdown_drops_empty_rows_and_columns():
    markdown = table_to_markdown([["A", "", "B"], ["", "", ""], ["1", "", "2"]])
    assert markdown == "| A | B |\n| --- | --- |\n| 1 | 2 |"


def test_a_single_row_or_column_is_returned_as_plain_text():
    assert table_to_markdown([["Satu", "Dua"]]) == "Satu Dua"
    assert table_to_markdown([["Satu"], ["Dua"]]) == "Satu Dua"
    assert table_to_markdown([[None, ""]]) == ""


# --- extract_pdf --------------------------------------------------------------------------------

def test_extract_pdf_keeps_the_table_whole_as_markdown():
    result = extract_pdf(build_pdf())

    tables = [b for p in result.pages for b in p.blocks if b.kind == "table"]
    assert len(tables) == 1
    assert tables[0].text.splitlines()[0] == "| Elemen | Capaian |"
    assert "| Pemahaman | Menjelaskan konsep ekonomi |" in tables[0].text
    assert "| Keterampilan | Menyajikan data pasar |" in tables[0].text


def test_table_text_is_not_duplicated_in_the_prose():
    result = extract_pdf(build_pdf())
    prose = " ".join(b.text for p in result.pages for b in p.blocks if b.kind == "text")
    assert "Menjelaskan konsep ekonomi" not in prose
    assert "interaksi antarpelaku ekonomi" in prose


def test_headings_carry_larger_bold_font_information():
    result = extract_pdf(build_pdf())
    blocks = [b for p in result.pages for b in p.blocks if b.kind == "text"]
    heading = next(b for b in blocks if b.text.startswith("Elemen Pemahaman"))
    body = next(b for b in blocks if b.text.startswith("Peserta didik"))

    assert heading.bold and not body.bold
    assert heading.font_size > body.font_size


def test_blocks_are_in_reading_order():
    result = extract_pdf(build_pdf())
    kinds = [b.kind for b in result.pages[0].blocks]
    assert kinds == ["text", "text", "table"]  # heading, paragraph, table


def test_a_page_without_text_is_reported():
    result = extract_pdf(blank_pdf())
    assert not result.has_text
    assert any("Halaman 1" in warning for warning in result.warnings)


def test_pages_without_text_lists_only_the_empty_pages():
    assert extract_pdf(blank_pdf(3)).pages_without_text == [1, 2, 3]
    assert extract_pdf(build_pdf()).pages_without_text == []


def test_unreadable_input_raises():
    import pytest
    with pytest.raises(Exception):
        extract_pdf(b"this is not a pdf")
