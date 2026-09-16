import re
from typing import List, Dict, Any

def semantic_chunk_text(pages: List[Dict[str, Any]], max_chars: int = 1500) -> List[Dict[str, Any]]:
    """
    Splits text by semantic boundaries (double newlines / paragraphs).
    Avoids splitting mid-sentence by prioritizing paragraph breaks.

    Accepts a list of dictionaries with 'page_number' and 'text'.
    Returns a list of dictionaries with 'page_number' and 'text', where 'text' is the chunk.
    """
    chunks = []

    for page in pages:
        page_number = page.get("page_number", 1)
        page_text = page.get("text", "")

        paragraphs = re.split(r'\n\s*\n', page_text.strip())

        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current_length + len(para) > max_chars and current_chunk:
                chunks.append({
                    "page_number": page_number,
                    "text": "\n\n".join(current_chunk)
                })
                current_chunk = []
                current_length = 0

            current_chunk.append(para)
            current_length += len(para)

        if current_chunk:
            chunks.append({
                "page_number": page_number,
                "text": "\n\n".join(current_chunk)
            })

    return chunks
