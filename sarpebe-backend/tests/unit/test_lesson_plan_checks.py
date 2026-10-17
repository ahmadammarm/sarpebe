import pytest

from app.core.services.lesson_plan_checks import build_references, check_modul, sanitize_sources
from app.schemas.lesson_plan_content import GeneratedModul
from tests.factories import activities_table, make_modul_dict, make_passage, make_request


def modul(**overrides) -> GeneratedModul:
    return GeneratedModul.model_validate(make_modul_dict(**overrides))


# --- sources -----------------------------------------------------------------------------------------------

def test_invented_source_ids_are_dropped_and_counted():
    result = modul()
    result.learning_objectives[0].source_ids = ["S1", "S9", "X"]

    dropped = sanitize_sources(result, {"S1", "S2"})

    assert dropped == 2
    assert result.learning_objectives[0].source_ids == ["S1"]
    assert result.learning_objectives[0].grounded is True


def test_an_objective_left_without_any_valid_source_is_marked_ungrounded():
    result = modul()
    result.learning_objectives[0].source_ids = ["S9"]

    sanitize_sources(result, {"S1"})

    assert result.learning_objectives[0].source_ids == []
    assert result.learning_objectives[0].grounded is False


def test_duplicate_source_ids_are_collapsed():
    result = modul()
    result.learning_objectives[0].source_ids = ["S1", "S1"]
    assert sanitize_sources(result, {"S1"}) == 1
    assert result.learning_objectives[0].source_ids == ["S1"]


def test_references_come_from_retrieved_passages_in_order_of_first_use():
    result = modul()
    result.learning_objectives[0].source_ids = ["S2", "S1"]
    result.learning_objectives[1].source_ids = ["S1", "S3"]
    passages = [
        make_passage("S1", document_title="CP IPS.pdf", page=14),
        make_passage("S2", document_title="ATP IPS.pdf", page=3, heading=None),
        make_passage("S3", document_title="CP IPS.pdf", page=20),
        make_passage("S4", document_title="Tidak dipakai.pdf"),
    ]

    references = build_references(result, passages)

    assert [r.id for r in references] == ["S2", "S1", "S3"]
    assert (references[0].document_title, references[0].page, references[0].heading) == ("ATP IPS.pdf", 3, None)


def test_references_ignore_ids_that_were_never_retrieved():
    result = modul()
    result.learning_objectives[0].source_ids = ["S7"]
    assert build_references(result, [make_passage("S1")]) == []


# --- checks ---------------------------------------------------------------------------------------------------

def test_a_correct_module_has_no_problems():
    report = check_modul(modul(), make_request())
    assert report.problems == []
    assert (report.grounded_objectives, report.total_objectives) == (1, 2)


def test_the_wrong_number_of_meetings_is_a_hard_problem():
    report = check_modul(modul(meetings=1), make_request(meeting_count=2))
    assert any("Jumlah pertemuan 1, seharusnya tepat 2" in p for p in report.hard)


def test_minutes_that_do_not_add_up_are_a_soft_problem_naming_the_meeting():
    data = make_modul_dict()
    data["meetings"][1]["activities"] = activities_table(minutes=(15, 50, 10))  # 75
    report = check_modul(GeneratedModul.model_validate(data), make_request())

    assert report.hard == []
    assert report.soft == ["Pertemuan 2: total waktu kegiatan 75 menit, seharusnya 80 menit."]


@pytest.mark.parametrize("cell,fits", [("15", True), ("15 menit", True), ("sekitar 15", True), ("lima belas", False), ("", False)])
def test_minutes_cells_may_carry_a_unit_but_must_contain_a_number(cell, fits):
    data = make_modul_dict(meetings=1)
    data["meetings"][0]["activities"]["rows"][0][1] = cell
    report = check_modul(GeneratedModul.model_validate(data), make_request(meeting_count=1))

    unreadable = [p for p in report.soft if "satu angka bulat" in p]
    assert (not unreadable) == fits


def test_a_table_without_a_time_column_is_reported():
    data = make_modul_dict(meetings=1)
    table = data["meetings"][0]["activities"]
    table["columns"] = ["Tahap", "Kegiatan", "Metode"]
    table["rows"] = [[row[0], row[2], row[3]] for row in table["rows"]]
    report = check_modul(GeneratedModul.model_validate(data), make_request(meeting_count=1))
    assert any("tidak punya kolom Waktu" in p for p in report.soft)


def test_too_few_activity_rows_is_a_soft_problem():
    data = make_modul_dict(meetings=1)
    data["meetings"][0]["activities"]["rows"] = data["meetings"][0]["activities"]["rows"][:2]
    report = check_modul(GeneratedModul.model_validate(data), make_request(meeting_count=1, minutes_per_meeting=70))
    assert any("pendahuluan, inti, dan penutup" in p for p in report.soft)


def test_an_empty_activity_table_is_a_hard_problem():
    data = make_modul_dict(meetings=1)
    data["meetings"][0]["activities"]["rows"] = []
    report = check_modul(GeneratedModul.model_validate(data), make_request(meeting_count=1))
    assert any("tabel kegiatan kosong" in p for p in report.hard)


def test_no_objectives_is_a_hard_problem():
    report = check_modul(modul(learning_objectives=[]), make_request())
    assert "Tujuan pembelajaran kosong." in report.hard


def test_objectives_without_any_source_are_a_hard_problem():
    data = make_modul_dict()
    for objective in data["learning_objectives"]:
        objective["source_ids"] = []
        objective["grounded"] = False
    report = check_modul(GeneratedModul.model_validate(data), make_request())
    assert any("source_ids" in p for p in report.hard)


def test_an_empty_rubric_is_a_hard_problem_but_an_empty_overview_is_soft():
    data = make_modul_dict()
    data["assessment"]["rubric"]["rows"] = []
    data["assessment"]["overview"]["rows"] = []
    report = check_modul(GeneratedModul.model_validate(data), make_request())
    assert "Rubrik penilaian kosong." in report.hard
    assert "Tabel ringkasan asesmen kosong." in report.soft
