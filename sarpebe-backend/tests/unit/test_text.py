import pytest

from app.utils.text import FILENAME_MAX_STEM, safe_filename


def test_spaces_become_underscores_and_the_extension_is_added():
    assert safe_filename("Modul Ajar Ekonomi", "pdf") == "Modul_Ajar_Ekonomi.pdf"


def test_accents_are_folded_to_their_base_letter():
    assert safe_filename("Café Résumé", "docx") == "Cafe_Resume.docx"


@pytest.mark.parametrize("stem", [
    'Laut "Jawa"',
    "a/b\\c",
    "tema; kedua",
    "baris\r\nbaru",
    "../../etc/passwd",
])
def test_characters_that_break_a_header_or_a_path_never_survive(stem):
    name = safe_filename(stem, "pdf")
    assert name.endswith(".pdf")
    assert not set(name) & set('"/\\;:\r\n \t')
    assert not name.startswith(".")


def test_a_long_topic_is_cut_before_the_extension():
    name = safe_filename("a" * 500, "pdf")
    assert name == "a" * FILENAME_MAX_STEM + ".pdf"


@pytest.mark.parametrize("stem", ["", "   ", "???", "日本語"])
def test_a_name_with_nothing_usable_falls_back(stem):
    assert safe_filename(stem, "pdf") == "Modul_Ajar.pdf"


def test_a_leading_dot_in_the_extension_is_ignored():
    assert safe_filename("Modul", ".pdf") == "Modul.pdf"
