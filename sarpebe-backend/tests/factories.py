"""Builders for valid Modul Ajar data, shared by the generation, checks, PDF and service tests."""
import copy
import uuid
from typing import Any

from app.core.prompts.lesson_plan import ModulRequest
from app.core.services.retrieval.types import Passage
from app.schemas.lesson_plan_content import ACTIVITY_COLUMNS, OVERVIEW_COLUMNS, RUBRIC_COLUMNS


def make_request(**overrides: Any) -> ModulRequest:
    values: dict[str, Any] = dict(
        grade_level="9",
        fase="D",
        subject="IPS",
        topic="Pelaku dan kegiatan ekonomi",
        meeting_count=2,
        minutes_per_meeting=80,
        teaching_model="otomatis",
        class_notes="",
    )
    values.update(overrides)
    return ModulRequest(**values)


def make_passage(passage_id: str = "S1", **overrides: Any) -> Passage:
    values: dict[str, Any] = dict(
        id=passage_id,
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title="CP IPS.pdf",
        page=14,
        page_end=14,
        heading="Elemen Pemahaman",
        text="Peserta didik mampu menganalisis interaksi antarpelaku ekonomi.",
        similarity=0.8,
        rerank_score=3,
        chunk_type="text",
    )
    values.update(overrides)
    return Passage(**values)


def activities_table(minutes: tuple[int, int, int] = (15, 55, 10)) -> dict[str, Any]:
    opening, core, closing = minutes
    return {
        "caption": "Kegiatan pembelajaran",
        "columns": list(ACTIVITY_COLUMNS),
        "rows": [
            ["Pendahuluan", str(opening), "Guru menanyakan pelaku ekonomi yang ditemui hari ini.", "Tanya jawab"],
            ["Inti", str(core), "Kelompok memetakan alur produksi, distribusi, dan konsumsi satu barang.", "Diskusi kelompok"],
            ["Penutup", str(closing), "Peserta didik menulis satu refleksi singkat.", "Refleksi"],
        ],
    }


def make_modul_dict(meetings: int = 2, **overrides: Any) -> dict[str, Any]:
    """What the model returns for a valid module (2 meetings of 80 minutes by default)."""
    data: dict[str, Any] = {
        "insufficient_context": False,
        "insufficient_reason": "",
        "title": "Pelaku dan Kegiatan Ekonomi di Sekitar Kita",
        "initial_competencies": ["Mengenal konsep kebutuhan dan keinginan."],
        "pancasila_profile": [
            {"dimension": "Bernalar Kritis", "how": "Menganalisis alur ekonomi sebuah barang."},
            {"dimension": "Bergotong Royong", "how": "Bekerja dalam kelompok memetakan alur."},
        ],
        "facilities": ["Ruang kelas dengan papan tulis", "Proyektor"],
        "target_students": "Peserta didik reguler tanpa kebutuhan khusus.",
        "learning_model": {"name": "Diskusi kelompok", "rationale": "Topik menuntut perbandingan sudut pandang."},
        "learning_objectives": [
            {
                "text": "Peserta didik mampu menganalisis interaksi antarpelaku ekonomi.",
                "source_ids": ["S1"],
                "grounded": True,
            },
            {"text": "Peserta didik mampu menyajikan contoh kegiatan ekonomi sekitar.", "source_ids": [], "grounded": False},
        ],
        "meaningful_understanding": ["Setiap orang berperan dalam rantai ekonomi."],
        "trigger_questions": ["Dari mana sepatu yang kamu pakai berasal?"],
        "preparation": ["Siapkan lembar kerja dan data pasar setempat."],
        "meetings": [
            {"number": number, "title": f"Pertemuan {number}", "activities": activities_table()}
            for number in range(1, meetings + 1)
        ],
        "assessment": {
            "diagnostic": {"technique": "Tanya jawab", "instrument": "Pertanyaan lisan", "description": "Memetakan pengetahuan awal."},
            "formative": {"technique": "Observasi", "instrument": "Lembar observasi", "description": "Mengamati diskusi kelompok."},
            "summative": {"technique": "Presentasi", "instrument": "Rubrik", "description": "Menilai peta alur akhir."},
            "overview": {
                "caption": "Ringkasan asesmen",
                "columns": list(OVERVIEW_COLUMNS),
                "rows": [["Diagnostik", "Tanya jawab", "Pertanyaan lisan", "Awal"], ["Sumatif", "Presentasi", "Rubrik", "Akhir"]],
            },
            "rubric": {
                "caption": "Rubrik penilaian peta alur",
                "columns": list(RUBRIC_COLUMNS),
                "rows": [["Ketepatan alur", "Semua tahap tepat", "Satu tahap keliru", "Dua tahap keliru", "Banyak keliru"]],
            },
        },
        "enrichment": ["Menganalisis dampak harga bahan baku pada alur.", "Membuat infografis alur."],
        "remedial": ["Menyusun ulang alur satu barang dengan bimbingan.", "Latihan memilah produksi dan konsumsi."],
        "reflection": {"teacher": ["Bagian mana yang paling sulit dipahami?"], "students": ["Apa yang baru kamu pahami?"]},
        "attachments": {
            "worksheet": {
                "title": "Peta alur barang",
                "instructions": "Kerjakan berkelompok.",
                "tasks": ["Pilih satu barang.", "Gambarkan alur produksinya.", "Jelaskan peran tiap pelaku."],
            },
            "reading_material": "Kegiatan ekonomi terdiri atas produksi – distribusi – konsumsi.\nSetiap tahap saling terhubung.",
            "glossary": [{"term": "Produksi", "definition": "Kegiatan menghasilkan barang atau jasa."}],
        },
    }
    data.update(copy.deepcopy(overrides))
    return data
