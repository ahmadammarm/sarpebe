from xml.sax.saxutils import escape, quoteattr


def escape_data(text: str) -> str:
    """
    Makes untrusted text safe to place between our own XML-style tags.
    Escaping `<`, `>` and `&` means text from a PDF or from a teacher can never close a tag
    (for example a literal "</sumber>") and start pretending to be instructions.
    """
    return escape(text)


def attribute(value: object) -> str:
    """An escaped, quoted attribute value, e.g. `"CP IPS &amp; PKn.pdf"`."""
    return quoteattr(str(value))
