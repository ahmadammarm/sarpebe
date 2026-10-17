"""
Checks on a generated Modul Ajar that the JSON schema cannot express, run in code so that a
wrong answer is caught (and repaired once) instead of being saved.

Problems come in two kinds. A *hard* problem makes the document unusable (no objectives, the wrong
number of meetings, nothing grounded in the sources). A *soft* problem is something a teacher can
fix in the editor (a meeting whose minutes add up to 75 instead of 80); if it survives the repair
attempt it is kept and shown as a warning.
"""
import re
from dataclasses import dataclass, field

from app.core.prompts.lesson_plan import ModulRequest
from app.core.services.retrieval.types import Passage
from app.schemas.lesson_plan_content import GeneratedModul, Reference

MIN_ACTIVITY_ROWS = 3  # pendahuluan, inti, penutup

_FIRST_NUMBER = re.compile(r"\d+")


@dataclass
class CheckReport:
    hard: list[str] = field(default_factory=list)
    soft: list[str] = field(default_factory=list)
    dropped_source_ids: int = 0
    grounded_objectives: int = 0
    total_objectives: int = 0

    @property
    def problems(self) -> list[str]:
        return [*self.hard, *self.soft]


def sanitize_sources(modul: GeneratedModul, valid_ids: set[str]) -> int:
    """
    Removes source ids the model made up (anything not among the passages it was given) and marks
    objectives that are left without a valid source as not grounded. Returns how many were dropped.
    """
    dropped = 0
    for objective in modul.learning_objectives:
        valid = []
        for source_id in objective.source_ids:
            if source_id in valid_ids and source_id not in valid:
                valid.append(source_id)
            else:
                dropped += 1
        objective.source_ids = valid
        if not valid:
            objective.grounded = False
    return dropped


def _minutes_column(columns: list[str]) -> int | None:
    for index, name in enumerate(columns):
        lowered = name.casefold()
        if "waktu" in lowered or "menit" in lowered:
            return index
    return None


def _meeting_minutes(rows: list[list[str]], column: int) -> tuple[int, bool]:
    """Sum of the minutes column, and whether every cell held a number."""
    total = 0
    readable = True
    for row in rows:
        match = _FIRST_NUMBER.search(row[column]) if column < len(row) else None
        if match is None:
            readable = False
        else:
            total += int(match.group())
    return total, readable


def check_modul(modul: GeneratedModul, request: ModulRequest) -> CheckReport:
    report = CheckReport(
        total_objectives=len(modul.learning_objectives),
        grounded_objectives=sum(1 for o in modul.learning_objectives if o.source_ids),
    )

    if not modul.learning_objectives:
        report.hard.append("Tujuan pembelajaran kosong.")
    elif report.grounded_objectives == 0:
        report.hard.append(
            "Tidak ada tujuan pembelajaran yang mencantumkan source_ids dari <sumber>. "
            "Setiap tujuan harus bertumpu pada sumber yang diberikan."
        )

    if len(modul.meetings) != request.meeting_count:
        report.hard.append(
            f"Jumlah pertemuan {len(modul.meetings)}, seharusnya tepat {request.meeting_count}."
        )

    for meeting in modul.meetings:
        table = meeting.activities
        label = f"Pertemuan {meeting.number}"
        if not table.rows:
            report.hard.append(f"{label}: tabel kegiatan kosong.")
            continue

        if len(table.rows) < MIN_ACTIVITY_ROWS:
            report.soft.append(f"{label}: kegiatan hanya {len(table.rows)} baris; harus memuat pendahuluan, inti, dan penutup.")

        column = _minutes_column(table.columns)
        if column is None:
            report.soft.append(f"{label}: tabel kegiatan tidak punya kolom Waktu (menit).")
            continue
        total, readable = _meeting_minutes(table.rows, column)
        if not readable:
            report.soft.append(f"{label}: kolom Waktu harus berisi satu angka bulat di setiap baris.")
        elif total != request.minutes_per_meeting:
            report.soft.append(
                f"{label}: total waktu kegiatan {total} menit, seharusnya {request.minutes_per_meeting} menit."
            )

    if not modul.assessment.rubric.rows:
        report.hard.append("Rubrik penilaian kosong.")
    if not modul.assessment.overview.rows:
        report.soft.append("Tabel ringkasan asesmen kosong.")
    if not modul.attachments.worksheet.tasks:
        report.soft.append("LKPD tidak memuat tugas.")

    return report


def build_references(modul: GeneratedModul, passages: list[Passage]) -> list[Reference]:
    """
    The reference list shown with the module, built from the passages the objectives actually cite.
    It comes from our retrieval records, not from text the model wrote, so every reference points
    at a real document page.
    """
    by_id = {passage.id: passage for passage in passages}
    ordered_ids: list[str] = []
    for objective in modul.learning_objectives:
        for source_id in objective.source_ids:
            if source_id in by_id and source_id not in ordered_ids:
                ordered_ids.append(source_id)

    return [
        Reference(
            id=source_id,
            document_title=by_id[source_id].document_title,
            page=by_id[source_id].page,
            page_end=by_id[source_id].page_end,
            heading=by_id[source_id].heading,
        )
        for source_id in ordered_ids
    ]
