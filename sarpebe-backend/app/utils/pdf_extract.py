"""
Reads a curriculum PDF into ordered blocks of text and tables.

pypdf returns a flat stream of text, which scrambles the tables that CP documents are full of.
pdfplumber can find ruled tables, so tables are rendered as Markdown (kept whole as chunks later)
and the remaining text is grouped into paragraphs with its font size, which the chunker uses to
spot headings. If pdfplumber fails on a file, the old pypdf path is used instead.
"""
import io
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal

import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)

_LIST_MARKER = re.compile(r"^(?:[-•*▪●○]|\d{1,2}[.)]|[a-zA-Z][.)])\s+")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Block:
    kind: Literal["text", "table"]
    text: str
    page: int
    top: float  # distance from the top of the page, used to restore reading order
    font_size: float | None = None  # None when unknown (e.g. the pypdf fallback)
    bold: bool = False


@dataclass
class ExtractedPage:
    number: int
    blocks: list[Block]


@dataclass
class ExtractionResult:
    pages: list[ExtractedPage]
    warnings: list[str] = field(default_factory=list)
    used_fallback: bool = False

    @property
    def has_text(self) -> bool:
        return any(block.text.strip() for page in self.pages for block in page.blocks)


# --- Tables -----------------------------------------------------------------------------------

def _clean_cell(value: str | None) -> str:
    return _WHITESPACE.sub(" ", (value or "").replace("|", "\\|")).strip()


def table_to_markdown(rows: list[list[str | None]]) -> str:
    """
    Renders extracted table rows as a Markdown table. Returns plain joined text when the
    "table" is really one row or one column (pdfplumber sometimes reports a framed paragraph).
    Cells that pdfplumber reports as None inside a merged span are filled from the cell above.
    """
    filled: list[list[str | None]] = []
    last: dict[int, str | None] = {}
    for row in rows:
        new_row: list[str | None] = []
        for index, cell in enumerate(row):
            if cell is None and last.get(index) is not None:
                new_row.append(last[index])
            else:
                new_row.append(cell)
                last[index] = cell
        filled.append(new_row)

    cleaned = [[_clean_cell(cell) for cell in row] for row in filled]
    cleaned = [row for row in cleaned if any(row)]
    if not cleaned:
        return ""

    width = max(len(row) for row in cleaned)
    cleaned = [row + [""] * (width - len(row)) for row in cleaned]
    keep = [i for i in range(width) if any(row[i] for row in cleaned)]
    cleaned = [[row[i] for i in keep] for row in cleaned]

    if len(cleaned) < 2 or len(keep) < 2:
        return " ".join(cell for row in cleaned for cell in row if cell)

    header, *body = cleaned
    header = [cell or f"Kolom {i + 1}" for i, cell in enumerate(header)]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


# --- Text -------------------------------------------------------------------------------------

def _is_bold(fontname: str | None) -> bool:
    return bool(fontname) and any(tag in fontname.lower() for tag in ("bold", "black", "heavy", "semibold"))


def _words_to_lines(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Groups words into visual lines by vertical position."""
    lines: list[dict[str, Any]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        height = max(word["bottom"] - word["top"], 1.0)
        if lines and abs(word["top"] - lines[-1]["top"]) <= max(2.0, height * 0.5):
            line = lines[-1]
            line["words"].append(word)
            line["bottom"] = max(line["bottom"], word["bottom"])
        else:
            lines.append({"top": word["top"], "bottom": word["bottom"], "words": [word]})

    result = []
    for line in lines:
        ordered = sorted(line["words"], key=lambda w: w["x0"])
        sizes = [w.get("size") or 0 for w in ordered]
        result.append({
            "text": " ".join(w["text"] for w in ordered),
            "top": line["top"],
            "bottom": line["bottom"],
            "size": max(sizes) if any(sizes) else None,
            "bold": all(_is_bold(w.get("fontname")) for w in ordered),
        })
    return result


def _lines_to_blocks(lines: list[dict[str, Any]], page: int) -> list[Block]:
    """Groups lines into paragraphs: a gap, or a change of font size or weight, starts a new one."""
    groups: list[list[dict[str, Any]]] = []
    for line in lines:
        if groups:
            previous = groups[-1][-1]
            line_height = max(previous["bottom"] - previous["top"], 1.0)
            gap = line["top"] - previous["bottom"]
            size_changed = (
                line["size"] is not None
                and previous["size"] is not None
                and abs(line["size"] - previous["size"]) > 1.0
            )
            if gap > line_height * 0.6 or size_changed or line["bold"] != previous["bold"]:
                groups.append([line])
                continue
            groups[-1].append(line)
        else:
            groups.append([line])

    blocks = []
    for group in groups:
        parts = [group[0]["text"]]
        for line in group[1:]:
            # Wrapped lines are re-joined into one flowing paragraph; list items keep their line break.
            parts.append(("\n" if _LIST_MARKER.match(line["text"]) else " ") + line["text"])
        text = "".join(parts).strip()
        if not text:
            continue
        sizes = [line["size"] for line in group if line["size"] is not None]
        blocks.append(Block(
            kind="text",
            text=text,
            page=page,
            top=group[0]["top"],
            font_size=max(sizes) if sizes else None,
            bold=all(line["bold"] for line in group),
        ))
    return blocks


def _outside(bboxes: list[tuple[float, float, float, float]]):
    """Predicate for Page.filter: drops characters that lie inside any table area."""
    def keep(obj: dict[str, Any]) -> bool:
        if obj.get("object_type") != "char":
            return True
        x = (obj["x0"] + obj["x1"]) / 2
        y = (obj["top"] + obj["bottom"]) / 2
        return not any(x0 <= x <= x1 and top <= y <= bottom for x0, top, x1, bottom in bboxes)
    return keep


def _extract_page(page: Any, number: int, warnings: list[str]) -> ExtractedPage:
    if not page.chars:
        warnings.append(f"Halaman {number} tidak berisi teks yang bisa dibaca (kemungkinan hasil pindai).")
        return ExtractedPage(number=number, blocks=[])

    blocks: list[Block] = []
    bboxes: list[tuple[float, float, float, float]] = []
    for table in page.find_tables():
        markdown = table_to_markdown(table.extract())
        if not markdown:
            continue
        bboxes.append(table.bbox)
        is_table = markdown.startswith("|")
        blocks.append(Block(kind="table" if is_table else "text", text=markdown, page=number, top=table.bbox[1]))

    area = page.filter(_outside(bboxes)) if bboxes else page
    words = area.extract_words(extra_attrs=["size", "fontname"], keep_blank_chars=False, x_tolerance=2, y_tolerance=3)
    blocks.extend(_lines_to_blocks(_words_to_lines(words), number))

    blocks.sort(key=lambda block: block.top)
    return ExtractedPage(number=number, blocks=blocks)


# --- Entry points -----------------------------------------------------------------------------

def _extract_with_pypdf(pdf_bytes: bytes) -> ExtractionResult:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages: list[ExtractedPage] = []
    warnings: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            warnings.append(f"Halaman {index} tidak berisi teks yang bisa dibaca (kemungkinan hasil pindai).")
            pages.append(ExtractedPage(number=index, blocks=[]))
            continue
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        pages.append(ExtractedPage(
            number=index,
            blocks=[Block(kind="text", text=p, page=index, top=float(i)) for i, p in enumerate(paragraphs)],
        ))
    return ExtractionResult(pages=pages, warnings=warnings, used_fallback=True)


def extract_pdf(pdf_bytes: bytes) -> ExtractionResult:
    """Extracts a PDF with table awareness, falling back to plain text if pdfplumber fails."""
    try:
        pages: list[ExtractedPage] = []
        warnings: list[str] = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                pages.append(_extract_page(page, number, warnings))
        return ExtractionResult(pages=pages, warnings=warnings)
    except Exception:
        logger.exception("pdfplumber could not read the file; falling back to pypdf")
        return _extract_with_pypdf(pdf_bytes)
