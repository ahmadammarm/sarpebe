from app.utils.chunking import semantic_chunk_text

def test_semantic_chunk_text_normal():
    text = "Paragraph 1.\n\nParagraph 2."
    chunks = semantic_chunk_text(text, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == "Paragraph 1.\n\nParagraph 2."

def test_semantic_chunk_text_exceeds_max():
    text = "A" * 1000 + "\n\n" + "B" * 1000
    chunks = semantic_chunk_text(text, max_chars=1500)
    assert len(chunks) == 2
    assert chunks[0] == "A" * 1000
    assert chunks[1] == "B" * 1000

def test_semantic_chunk_text_empty():
    assert semantic_chunk_text("") == []
    assert semantic_chunk_text("   \n  \n ") == []

def test_semantic_chunk_text_no_newlines():
    text = "A" * 2000
    chunks = semantic_chunk_text(text, max_chars=1500)
    # It won't split mid-sentence right now because it splits by double newlines.
    # So it should return a single chunk that exceeds max_chars.
    assert len(chunks) == 1
    assert chunks[0] == "A" * 2000
