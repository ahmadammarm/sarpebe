from app.utils.chunking import chunk_document, semantic_chunk_text, split_oversize
from app.utils.pdf_extract import Block, ExtractedPage, ExtractionResult


def text_block(text, page=1, top=0.0, size=11.0, bold=False):
    return Block(kind="text", text=text, page=page, top=top, font_size=size, bold=bold)


def table_block(markdown, page=1, top=0.0):
    return Block(kind="table", text=markdown, page=page, top=top)


def document(*pages_blocks):
    return ExtractionResult(
        pages=[ExtractedPage(number=i, blocks=list(blocks)) for i, blocks in enumerate(pages_blocks, start=1)]
    )


BODY = "Peserta didik memahami konsep dasar dan menerapkannya dalam kehidupan sehari-hari secara mandiri."


# --- plain text wrapper ---------------------------------------------------------------------

def test_semantic_chunk_text_normal():
    chunks = semantic_chunk_text([{"page_number": 1, "text": "Paragraph 1.\n\nParagraph 2."}], max_chars=100)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Paragraph 1.\n\nParagraph 2."
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_type"] == "text"


def test_semantic_chunk_text_exceeds_max_splits_between_paragraphs():
    chunks = semantic_chunk_text([{"page_number": 1, "text": "A" * 1000 + "\n\n" + "B" * 1000}], max_chars=1500)
    assert [c["text"] for c in chunks] == ["A" * 1000, "B" * 1000]


def test_semantic_chunk_text_empty():
    assert semantic_chunk_text([]) == []
    assert semantic_chunk_text([{"page_number": 1, "text": "   \n  \n "}]) == []


def test_text_without_any_boundary_is_hard_split_under_the_limit():
    chunks = semantic_chunk_text([{"page_number": 1, "text": "A" * 4000}], max_chars=1500)
    assert len(chunks) >= 3
    assert all(len(c["text"]) <= 1500 for c in chunks)


# --- long paragraphs --------------------------------------------------------------------------

def test_oversize_paragraph_splits_at_sentences_with_overlap():
    sentences = [f"Kalimat nomor {i} membahas satu gagasan penting tentang ekonomi." for i in range(40)]
    pieces = split_oversize(" ".join(sentences), max_chars=600, overlap_chars=120)

    assert len(pieces) >= 3
    assert all(len(piece) <= 600 for piece in pieces)
    # The start of each piece repeats the end of the previous one.
    for previous, current in zip(pieces, pieces[1:]):
        first_words = " ".join(current.split()[:3])
        assert first_words in previous
    # Nothing is lost: every sentence survives intact in at least one piece.
    assert all(any(sentence in piece for piece in pieces) for sentence in sentences)
    assert "Kalimat nomor 39" in pieces[-1]


# --- headings ---------------------------------------------------------------------------------

def test_heading_is_attached_to_chunks_but_not_part_of_the_text():
    result = chunk_document(document([
        text_block("Elemen Pemahaman IPS", size=16, bold=True),
        text_block(BODY),
    ]))
    assert len(result) == 1
    assert result[0].heading == "Elemen Pemahaman IPS"
    assert "Elemen Pemahaman" not in result[0].text


def test_a_new_heading_starts_a_new_chunk():
    result = chunk_document(document([
        text_block("Elemen Pemahaman", size=16, bold=True),
        text_block(BODY, top=20),
        text_block("Elemen Keterampilan", size=16, bold=True, top=60),
        text_block(BODY + " Dilanjutkan dengan kegiatan.", top=80),
    ]))
    assert [c.heading for c in result] == ["Elemen Pemahaman", "Elemen Keterampilan"]


def test_subheading_is_nested_under_the_heading():
    result = chunk_document(document([
        text_block("Fase D", size=18, bold=True),
        text_block("Capaian Pembelajaran", size=14, bold=True, top=20),
        text_block(BODY, top=40),
    ]))
    assert result[0].heading == "Fase D > Capaian Pembelajaran"


def test_sentences_and_intro_lines_are_not_headings():
    result = chunk_document(document([
        text_block("Peserta didik mampu:", size=11),
        text_block("Ini kalimat biasa yang diakhiri titik.", top=20),
    ]))
    assert len(result) == 1
    assert result[0].heading is None


# --- tables -----------------------------------------------------------------------------------

TABLE = "| Elemen | Capaian |\n| --- | --- |\n| Pemahaman | Menjelaskan konsep |\n| Keterampilan | Menyajikan data |"


def test_table_is_its_own_chunk_and_flushes_the_text_before_it():
    result = chunk_document(document([
        text_block("Capaian Fase D", size=16, bold=True),
        text_block(BODY, top=20),
        table_block(TABLE, top=60),
        text_block(BODY + " Setelah tabel.", top=120),
    ]))
    assert [c.chunk_type for c in result] == ["text", "table", "text"]
    assert result[1].text == TABLE
    assert result[1].heading == "Capaian Fase D"


def test_very_large_table_is_split_by_rows_with_the_header_repeated():
    rows = "\n".join(f"| Baris {i} | {'isi ' * 20} |" for i in range(60))
    big = "| Kolom A | Kolom B |\n| --- | --- |\n" + rows
    result = chunk_document(document([table_block(big)]), max_table_chars=1000)

    assert len(result) > 1
    for chunk in result:
        assert chunk.chunk_type == "table"
        assert chunk.text.startswith("| Kolom A | Kolom B |\n| --- | --- |")
        assert len(chunk.text) <= 1000 + 200


# --- pages ------------------------------------------------------------------------------------

def test_a_chunk_can_span_pages_and_remembers_both():
    result = chunk_document(document(
        [text_block("Rasional", size=16, bold=True), text_block(BODY, top=20)],
        [text_block(BODY + " Lanjutan di halaman berikutnya.", page=2)],
    ))
    assert len(result) == 1
    assert (result[0].page_number, result[0].page_end) == (1, 2)


def test_intro_line_stays_with_the_list_it_introduces():
    intro = "Peserta didik mampu:"
    items = "\n".join(f"- melakukan kegiatan nomor {i} dengan baik" for i in range(18))
    result = chunk_document(document([text_block(intro), text_block(items, top=20)]), max_chars=500)
    assert intro in result[0].text
    assert "kegiatan nomor 0" in result[0].text
