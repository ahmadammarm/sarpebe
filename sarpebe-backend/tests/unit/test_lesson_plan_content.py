import json

import pytest
from pydantic import ValidationError

from app.schemas.json_schema import to_gemini_schema
from app.schemas.lesson_plan import LessonPlanCreate, TeachingModel
from app.schemas.lesson_plan_content import GeneratedModul, Identity, ModulContent, Table
from tests.factories import make_modul_dict


# --- Table -----------------------------------------------------------------------------------------

def test_table_accepts_rows_with_the_same_number_of_cells_as_columns():
    table = Table(caption="T", columns=["A", "B"], rows=[["1", "2"], ["3", "4"]])
    assert len(table.rows) == 2


def test_table_rejects_a_row_with_the_wrong_number_of_cells():
    with pytest.raises(ValidationError, match="baris 2 punya 1 sel, seharusnya 2"):
        Table(caption="T", columns=["A", "B"], rows=[["1", "2"], ["3"]])


def test_table_may_be_empty():
    assert Table(caption="T", columns=["A"], rows=[]).rows == []


# --- GeneratedModul / ModulContent ---------------------------------------------------------------------

def test_a_valid_module_validates():
    modul = GeneratedModul.model_validate(make_modul_dict())
    assert modul.meetings[0].activities.rows[0][0] == "Pendahuluan"
    assert modul.learning_objectives[0].source_ids == ["S1"]


def test_an_abstaining_answer_with_empty_sections_is_still_schema_valid():
    empty = make_modul_dict(meetings=0, insufficient_context=True, insufficient_reason="Sumber tidak memuat topik ini.")
    empty["learning_objectives"] = []
    empty["assessment"]["rubric"]["rows"] = []
    modul = GeneratedModul.model_validate(empty)
    assert modul.insufficient_context and modul.meetings == []


def test_an_unknown_pancasila_dimension_is_rejected():
    data = make_modul_dict()
    data["pancasila_profile"][0]["dimension"] = "Dimensi karangan"
    with pytest.raises(ValidationError):
        GeneratedModul.model_validate(data)


def test_a_missing_required_section_is_rejected():
    data = make_modul_dict()
    del data["assessment"]
    with pytest.raises(ValidationError):
        GeneratedModul.model_validate(data)


def test_stored_content_adds_identity_references_and_the_schema_version():
    identity = Identity(
        subject="IPS", grade_level="9", fase="D", topic="Ekonomi", meetings=2,
        minutes_per_meeting=80, teaching_model="otomatis",
    )
    content = ModulContent(**GeneratedModul.model_validate(make_modul_dict()).model_dump(), identity=identity)
    dumped = content.model_dump(mode="json")

    assert dumped["schema_version"] == 2
    assert dumped["references"] == [] and dumped["warnings"] == []
    assert ModulContent.model_validate(dumped) == content  # survives a save/load round trip


def test_stored_content_rejects_a_broken_table_edit():
    stored = ModulContent(
        **GeneratedModul.model_validate(make_modul_dict()).model_dump(),
        identity=Identity(subject="IPS", grade_level="9", topic="x", meetings=2, minutes_per_meeting=80, teaching_model="otomatis"),
    ).model_dump(mode="json")
    stored["meetings"][0]["activities"]["rows"][0].pop()  # a teacher deleted a cell

    with pytest.raises(ValidationError):
        ModulContent.model_validate(stored)


# --- the JSON Schema sent to the model ----------------------------------------------------------------------

def test_the_model_schema_is_plain_json_and_has_no_noise_keywords():
    schema = to_gemini_schema(GeneratedModul)
    json.dumps(schema)  # serializable

    def walk(node, path="$"):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("properties", "$defs"):
                    for name, child in value.items():
                        yield from walk(child, f"{path}.{key}.{name}")
                else:
                    yield path, key
                    yield from walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                yield from walk(child, f"{path}[{index}]")

    keywords = {key for _, key in walk(schema)}
    assert "title" not in keywords and "default" not in keywords


def test_the_model_schema_requires_every_section_and_keeps_field_descriptions():
    schema = to_gemini_schema(GeneratedModul)
    assert set(schema["required"]) == set(GeneratedModul.model_fields)
    assert "Satu entri untuk setiap pertemuan" in schema["properties"]["meetings"]["description"]


def test_the_model_schema_does_not_ask_for_server_built_fields():
    properties = to_gemini_schema(GeneratedModul)["properties"]
    assert not {"identity", "references", "warnings", "schema_version"} & set(properties)


# --- request validation -----------------------------------------------------------------------------------

def test_request_defaults_are_a_single_80_minute_meeting():
    payload = LessonPlanCreate(grade_level="9", subject="IPS", topic="Ekonomi")
    assert (payload.meeting_count, payload.minutes_per_meeting, payload.teaching_model) == (1, 80, TeachingModel.OTOMATIS)
    assert payload.class_notes == ""


@pytest.mark.parametrize("field,value", [
    ("meeting_count", 0), ("meeting_count", 7), ("minutes_per_meeting", 10), ("minutes_per_meeting", 300),
    ("teaching_model", "ceramah"), ("class_notes", "x" * 501),
])
def test_request_rejects_out_of_range_values(field, value):
    with pytest.raises(ValidationError):
        LessonPlanCreate(grade_level="9", subject="IPS", topic="Ekonomi", **{field: value})


def test_class_notes_are_trimmed():
    payload = LessonPlanCreate(grade_level="9", subject="IPS", topic="Ekonomi", class_notes="  kelas aktif  ")
    assert payload.class_notes == "kelas aktif"
