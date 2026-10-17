import re

_WHITESPACE = re.compile(r"\s+")


def normalize_label(value: str) -> str:
    """
    Canonical form of a grade/subject label used for exact-match pre-filtering,
    so that "Biologi", " biologi " and "BIOLOGI" all resolve to the same value.
    """
    return _WHITESPACE.sub(" ", value.strip()).casefold()
