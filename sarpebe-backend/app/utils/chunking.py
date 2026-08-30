import re

def semantic_chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    """
    Splits text by semantic boundaries (double newlines / paragraphs).
    Avoids splitting mid-sentence by prioritizing paragraph breaks.
    """
    paragraphs = re.split(r'\n\s*\n', text.strip())
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if current_length + len(para) > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_length = 0
            
        current_chunk.append(para)
        current_length += len(para)
        
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks
