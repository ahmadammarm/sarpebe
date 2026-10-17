import re

_WORD = re.compile(r"[^\W_]{3,}")


def keyword_terms(text: str, limit: int = 12) -> list[str]:
    """
    Distinct lower-cased words of at least three letters or digits, in order, for a full-text query.
    Only word characters survive, so the result is safe to join with " | " into a tsquery.
    """
    seen: dict[str, None] = {}
    for word in _WORD.findall(text.casefold()):
        seen.setdefault(word, None)
    return list(seen)[:limit]
