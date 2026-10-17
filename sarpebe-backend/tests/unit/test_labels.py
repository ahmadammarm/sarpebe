import pytest
from app.utils.labels import normalize_label

@pytest.mark.parametrize("raw,expected", [
    ("Biologi", "biologi"),
    ("  BIOLOGI  ", "biologi"),
    ("Ilmu   Pengetahuan\tAlam", "ilmu pengetahuan alam"),
    ("10", "10"),
])
def test_normalize_label(raw, expected):
    assert normalize_label(raw) == expected

def test_equivalent_spellings_match():
    assert normalize_label("Biologi") == normalize_label(" biologi ")
