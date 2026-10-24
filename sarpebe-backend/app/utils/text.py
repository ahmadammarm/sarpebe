import re
import unicodedata

_WORD = re.compile(r"[^\W_]{3,}")
_FILENAME_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
FILENAME_MAX_STEM = 80


def safe_filename(stem: str, extension: str, fallback: str = "Modul_Ajar") -> str:
    """
    A download name that is safe inside a Content-Disposition header: ASCII letters, digits,
    dot, dash and underscore only, at most FILENAME_MAX_STEM characters before the extension.
    Accents are folded to their base letter; anything else collapses to an underscore.
    """
    folded = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    cleaned = _FILENAME_UNSAFE.sub("_", folded).strip("._-")[:FILENAME_MAX_STEM].strip("._-")
    return f"{cleaned or fallback}.{extension.lstrip('.')}"


def keyword_terms(text: str, limit: int = 12) -> list[str]:
    """
    Distinct lower-cased words of at least three letters or digits, in order, for a full-text query.
    Only word characters survive, so the result is safe to join with " | " into a tsquery.
    """
    seen: dict[str, None] = {}
    for word in _WORD.findall(text.casefold()):
        seen.setdefault(word, None)
    return list(seen)[:limit]
