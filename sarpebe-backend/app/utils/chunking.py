import re
from typing import List, Dict, Any

def is_table_or_list_line(line: str) -> bool:
    """
    Checks if a line looks like part of a table row or bulleted/numbered list.
    """
    stripped = line.strip()
    # List patterns: "- ", "* ", "1. ", "a) ", etc.
    if re.match(r'^([-*•]|\d+[\.\)]|[a-zA-Z][\.\)])\s+', stripped):
        return True
    # Table row patterns: pipe delimiters "| col1 | col2 |"
    if stripped.startswith("|") and stripped.endswith("|"):
        return True
    # Markdown separator row "| --- | --- |"
    if re.match(r'^\|?\s*:?-+:?\s*\|', stripped):
        return True
    # Tab-separated or multiple multi-space columns
    if "\t" in stripped or re.search(r'\s{3,}', stripped):
        return True
    return False

def semantic_chunk_text(pages: List[Dict[str, Any]], max_chars: int = 1500) -> List[Dict[str, Any]]:
    """
    Splits text by semantic boundaries (headings, sections, paragraphs).
    Intelligently preserves markdown tables and bulleted/numbered lists so they are
    not split abruptly across chunk boundaries.

    Accepts a list of dictionaries with 'page_number' and 'text'.
    Returns a list of dictionaries with 'page_number' and 'text'.
    """
    chunks = []

    for page in pages:
        page_number = page.get("page_number", 1)
        page_text = page.get("text", "")

        raw_paragraphs = re.split(r'\n\s*\n', page_text.strip())

        # Group paragraphs while keeping lists and tables unified with their intro lines
        structured_blocks = []
        current_block = []

        for para in raw_paragraphs:
            lines = [line for line in para.split('\n') if line.strip()]
            if not lines:
                continue

            # If all or most lines are list items or table lines, treat as a structured block
            is_structured = any(is_table_or_list_line(line) for line in lines)

            if is_structured:
                # If current block has an introductory sentence, keep them together
                current_block.append(para.strip())
            else:
                if current_block:
                    structured_blocks.append("\n\n".join(current_block))
                    current_block = []
                current_block.append(para.strip())

        if current_block:
            structured_blocks.append("\n\n".join(current_block))

        # Chunk the structured blocks respecting max_chars
        current_chunk = []
        current_length = 0

        for block in structured_blocks:
            block_len = len(block)
            if current_length + block_len > max_chars and current_chunk:
                chunks.append({
                    "page_number": page_number,
                    "text": "\n\n".join(current_chunk)
                })
                current_chunk = []
                current_length = 0

            # If a single block itself exceeds max_chars, split it by sentences/newlines safely
            if block_len > max_chars:
                sub_lines = block.split('\n')
                sub_chunk = []
                sub_len = 0
                for s_line in sub_lines:
                    if sub_len + len(s_line) > max_chars and sub_chunk:
                        chunks.append({
                            "page_number": page_number,
                            "text": "\n".join(sub_chunk)
                        })
                        sub_chunk = []
                        sub_len = 0
                    sub_chunk.append(s_line)
                    sub_len += len(s_line) + 1
                if sub_chunk:
                    current_chunk.append("\n".join(sub_chunk))
                    current_length += sub_len
            else:
                current_chunk.append(block)
                current_length += block_len

        if current_chunk:
            chunks.append({
                "page_number": page_number,
                "text": "\n\n".join(current_chunk)
            })

    return chunks
