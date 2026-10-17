"""
Splits an extracted document into chunks for retrieval.

What a chunk is:
- Prose chunks hold whole paragraphs under one heading, up to `max_chars`. A paragraph longer than
  that is split at sentence boundaries and the pieces overlap slightly so a sentence is never the
  only thing that links two chunks.
- A table is its own chunk (split by rows, header repeated, only if it is very large).
- Every chunk remembers the heading it sits under and the pages it covers, so retrieval can cite
  "halaman 14, bagian Elemen Pemahaman".
"""
import re
import statistics
from dataclasses import dataclass
from typing import Any, Literal

from app.utils.pdf_extract import Block, ExtractedPage, ExtractionResult

MAX_CHARS = 1500
OVERLAP_CHARS = 150
MAX_TABLE_CHARS = 3000

_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+|\n")
_HEADING_KEYWORD = re.compile(r"^(?:BAB|Bagian|Elemen|Fase|Capaian|Tujuan|Lampiran|Rasional|Karakteristik)\b", re.IGNORECASE)
_NUMBERED = re.compile(r"^(?:[A-Z]\.|\d+(?:\.\d+)*[.)]?)\s+\S")


@dataclass(frozen=True)
class Chunk:
    text: str
    page_number: int
    page_end: int
    heading: str | None
    chunk_type: Literal["text", "table"]


# --- Headings ---------------------------------------------------------------------------------

def _body_font_size(extraction: ExtractionResult) -> float | None:
    """The typical font size of running text, so larger text can be recognized as a heading."""
    sizes = [
        block.font_size
        for page in extraction.pages
        for block in page.blocks
        if block.kind == "text" and block.font_size is not None and len(block.text) > 40
    ]
    return statistics.median(sizes) if sizes else None


def _is_heading(block: Block, body_size: float | None) -> bool:
    text = block.text.strip()
    if not text or "\n" in text or len(text) > 120:
        return False

    larger = body_size is not None and block.font_size is not None and block.font_size >= body_size * 1.12
    if larger and len(text) <= 100:
        return True

    # Sentences and intro lines ("Peserta didik mampu:") are not headings.
    if text.endswith((".", ":", ";", ",")) or len(text) > 90:
        return False

    letters = [c for c in text if c.isalpha()]
    all_caps = len(letters) >= 4 and sum(c.isupper() for c in letters) / len(letters) >= 0.8
    return (
        (block.bold and len(text) <= 100)
        or all_caps
        or bool(_HEADING_KEYWORD.match(text))
        or bool(_NUMBERED.match(text) and len(text) <= 80)
    )


def _heading_rank(block: Block) -> float:
    """Smaller = more important. Without font information every heading replaces the last one."""
    return -(block.font_size or 0.0)


# --- Splitting long text ----------------------------------------------------------------------

def _hard_split(text: str, max_chars: int) -> list[str]:
    """Last resort for text with no sentence boundaries: cut at the last space before the limit."""
    pieces = []
    rest = text.strip()
    while len(rest) > max_chars:
        cut = rest.rfind(" ", 0, max_chars)
        cut = cut if cut > max_chars // 2 else max_chars
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        pieces.append(rest)
    return pieces


def _tail(text: str, size: int) -> str:
    """The last ~`size` characters of `text`, starting at a word boundary."""
    if size <= 0 or len(text) <= size:
        return ""
    tail = text[-size:]
    space = tail.find(" ")
    return tail[space + 1:] if space != -1 else tail


def split_oversize(text: str, max_chars: int = MAX_CHARS, overlap_chars: int = OVERLAP_CHARS) -> list[str]:
    """
    Splits one long paragraph at sentence boundaries; every piece after the first starts with
    overlap. No piece is longer than `max_chars`, overlap included.
    """
    # Leave room for the overlap so that overlap + a unit always fits.
    unit_limit = max(max_chars - overlap_chars - 1, max_chars // 2)  # -1 for the joining space
    units: list[str] = []
    for unit in _SENTENCE_END.split(text):
        unit = unit.strip()
        if not unit:
            continue
        units.extend(_hard_split(unit, unit_limit) if len(unit) > unit_limit else [unit])

    pieces: list[str] = []
    current = ""
    for unit in units:
        if current and len(current) + 1 + len(unit) > max_chars:
            pieces.append(current)
            current = (_tail(current, overlap_chars) + " " + unit).strip()
        else:
            current = f"{current} {unit}".strip()
    if current:
        pieces.append(current)
    return pieces


# --- Tables -----------------------------------------------------------------------------------

def _split_table(markdown: str, max_chars: int) -> list[str]:
    """Splits a very large Markdown table by rows, repeating the header in every part."""
    if len(markdown) <= max_chars:
        return [markdown]

    lines = markdown.split("\n")
    header, rows = lines[:2], lines[2:]
    parts: list[str] = []
    current: list[str] = []
    size = sum(len(line) + 1 for line in header)
    for row in rows:
        if current and size + len(row) + 1 > max_chars:
            parts.append("\n".join(header + current))
            current, size = [], sum(len(line) + 1 for line in header)
        current.append(row)
        size += len(row) + 1
    if current:
        parts.append("\n".join(header + current))
    return parts


# --- Chunking ---------------------------------------------------------------------------------

class _Pending:
    """The prose chunk being built."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.length = 0
        self.page_start = 0
        self.page_end = 0
        self.heading: str | None = None

    def add(self, text: str, page: int, heading: str | None) -> None:
        if not self.parts:
            self.page_start = page
            self.heading = heading
        self.parts.append(text)
        self.page_end = page
        self.length += len(text) + 2

    def clear(self) -> None:
        self.__init__()


def chunk_document(
    extraction: ExtractionResult,
    *,
    max_chars: int = MAX_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
    max_table_chars: int = MAX_TABLE_CHARS,
) -> list[Chunk]:
    body_size = _body_font_size(extraction)
    chunks: list[Chunk] = []
    pending = _Pending()
    heading_path: list[tuple[float, str]] = []  # (rank, text), most important first

    def current_heading() -> str | None:
        return " > ".join(text for _, text in heading_path[-2:]) or None

    def flush() -> None:
        if pending.parts:
            chunks.append(Chunk(
                text="\n\n".join(pending.parts),
                page_number=pending.page_start,
                page_end=pending.page_end,
                heading=pending.heading,
                chunk_type="text",
            ))
        pending.clear()

    for page in extraction.pages:
        for block in page.blocks:
            text = block.text.strip()
            if not text:
                continue

            if block.kind == "table":
                flush()
                for part in _split_table(text, max_table_chars):
                    chunks.append(Chunk(part, block.page, block.page, current_heading(), "table"))
                continue

            if _is_heading(block, body_size):
                flush()
                rank = _heading_rank(block)
                while heading_path and heading_path[-1][0] >= rank:
                    heading_path.pop()
                heading_path.append((rank, text))
                continue

            heading = current_heading()
            if pending.parts and pending.heading != heading:
                flush()

            pieces = split_oversize(text, max_chars, overlap_chars) if len(text) > max_chars else [text]
            for piece in pieces:
                intro_pending = pending.parts and pending.parts[-1].rstrip().endswith(":")
                overflows = pending.length + len(piece) > max_chars
                # An intro line ending in ":" stays with what it introduces, within reason.
                if pending.parts and overflows and not (intro_pending and pending.length + len(piece) <= max_chars * 1.5):
                    flush()
                pending.add(piece, block.page, heading)

    flush()
    return chunks


def semantic_chunk_text(pages: list[dict[str, Any]], max_chars: int = MAX_CHARS) -> list[dict[str, Any]]:
    """
    Chunks plain page text ({"page_number", "text"}) without font information, so headings are
    found by their wording only. Kept for callers that have no PDF blocks.
    """
    extraction_pages = []
    for page in pages:
        number = page.get("page_number", 1)
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", page.get("text", "").strip()) if p.strip()]
        blocks = [Block(kind="text", text=p, page=number, top=float(i)) for i, p in enumerate(paragraphs)]
        extraction_pages.append(ExtractedPage(number=number, blocks=blocks))

    chunks = chunk_document(ExtractionResult(pages=extraction_pages), max_chars=max_chars)
    return [
        {
            "page_number": c.page_number,
            "page_end": c.page_end,
            "text": c.text,
            "heading": c.heading,
            "chunk_type": c.chunk_type,
        }
        for c in chunks
    ]
