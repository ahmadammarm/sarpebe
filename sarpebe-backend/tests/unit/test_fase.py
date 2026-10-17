import pytest

from app.utils.fase import FASES, fase_for_grade


@pytest.mark.parametrize("grade,code", [
    ("1", "A"), ("2", "A"), ("3", "B"), ("4", "B"), ("5", "C"), ("6", "C"),
    ("7", "D"), ("8", "D"), ("9", "D"), ("10", "E"), ("11", "F"), ("12", "F"),
])
def test_every_grade_maps_to_its_phase(grade, code):
    assert fase_for_grade(grade).code == code


@pytest.mark.parametrize("grade", ["", "0", "13", "99", "X", "kelas 9", "9a", "-3", "९"])
def test_anything_that_is_not_a_grade_from_1_to_12_has_no_phase(grade):
    assert fase_for_grade(grade) is None


def test_surrounding_whitespace_is_ignored():
    assert fase_for_grade(" 9 ").code == "D"


def test_phases_cover_grades_1_to_12_exactly_once():
    covered = [g for fase in FASES for g in range(fase.from_grade, fase.to_grade + 1)]
    assert covered == list(range(1, 13))
