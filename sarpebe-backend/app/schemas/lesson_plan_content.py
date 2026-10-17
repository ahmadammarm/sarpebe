"""
Content of a Modul Ajar (schema_version 2).

`GeneratedModul` is what the model must produce: its JSON Schema is sent to Gemini and the same
class validates the answer, so the two cannot drift apart. `ModulContent` is what is stored and
shown: the model's output plus what the server knows for certain (the request, the references
built from the retrieved passages, and any warnings). Field descriptions are instructions to the
model, so they are written for it.
"""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = 2

PancasilaDimensionName = Literal[
    "Beriman dan Bertakwa",
    "Berkebinekaan Global",
    "Bergotong Royong",
    "Mandiri",
    "Bernalar Kritis",
    "Kreatif",
]

ACTIVITY_COLUMNS = ["Tahap", "Waktu (menit)", "Kegiatan", "Metode"]
OVERVIEW_COLUMNS = ["Jenis", "Teknik", "Instrumen", "Waktu"]
RUBRIC_COLUMNS = ["Kriteria", "4 (Sangat baik)", "3 (Baik)", "2 (Cukup)", "1 (Perlu bimbingan)"]


class Table(BaseModel):
    caption: str = Field(description="Judul singkat tabel.")
    columns: list[str] = Field(description="Judul setiap kolom.")
    rows: list[list[str]] = Field(
        description="Baris data. Setiap baris memiliki jumlah sel yang sama dengan jumlah kolom; sel berisi teks singkat."
    )

    @model_validator(mode="after")
    def _rows_match_columns(self) -> "Table":
        for number, row in enumerate(self.rows, start=1):
            if len(row) != len(self.columns):
                raise ValueError(
                    f"tabel '{self.caption}': baris {number} punya {len(row)} sel, seharusnya {len(self.columns)}"
                )
        return self


class SourcedItem(BaseModel):
    text: str
    source_ids: list[str] = Field(
        description='Id sumber ("S1", "S2", ...) dari <sumber> yang mendasari butir ini. Kosong jika tidak ada.'
    )
    grounded: bool = Field(
        description="true jika butir ini langsung bersumber dari <sumber>; false jika rancangan Anda sendiri."
    )


class PancasilaDimension(BaseModel):
    dimension: PancasilaDimensionName
    how: str = Field(description="Bagaimana dimensi ini muncul dalam kegiatan pembelajaran.")


class LearningModel(BaseModel):
    name: str
    rationale: str = Field(description="Satu kalimat alasan memilih model ini untuk topik ini.")


class Meeting(BaseModel):
    number: int = Field(description="Nomor pertemuan, mulai dari 1.")
    title: str = Field(description="Judul atau fokus pertemuan.")
    activities: Table = Field(
        description="Tabel kegiatan dengan kolom: Tahap, Waktu (menit), Kegiatan, Metode. Memuat pendahuluan, inti, dan penutup."
    )


class AssessmentItem(BaseModel):
    technique: str
    instrument: str
    description: str


class Assessment(BaseModel):
    diagnostic: AssessmentItem
    formative: AssessmentItem
    summative: AssessmentItem
    overview: Table = Field(description="Ringkasan asesmen. Kolom: Jenis, Teknik, Instrumen, Waktu.")
    rubric: Table = Field(
        description="Rubrik penilaian. Kolom: Kriteria, 4 (Sangat baik), 3 (Baik), 2 (Cukup), 1 (Perlu bimbingan)."
    )


class Reflection(BaseModel):
    teacher: list[str] = Field(description="Pertanyaan refleksi untuk guru.")
    students: list[str] = Field(description="Pertanyaan refleksi untuk peserta didik.")


class Worksheet(BaseModel):
    title: str
    instructions: str
    tasks: list[str] = Field(description="Tugas bernomor untuk peserta didik, 3 sampai 6 butir.")


class GlossaryItem(BaseModel):
    term: str
    definition: str


class Attachments(BaseModel):
    worksheet: Worksheet = Field(description="Lembar Kerja Peserta Didik (LKPD).")
    reading_material: str = Field(description="Bahan bacaan singkat untuk peserta didik.")
    glossary: list[GlossaryItem] = Field(description="Glosarium 4 sampai 8 istilah.")


class GeneratedModul(BaseModel):
    """What the model writes. Identity, references and warnings are added by the server."""

    insufficient_context: bool = Field(
        description="true jika <sumber> tidak cukup untuk topik yang diminta. Jika true, kosongkan bagian lain."
    )
    insufficient_reason: str = Field(description="Satu kalimat alasan jika insufficient_context true; selain itu kosong.")
    title: str = Field(description="Judul modul ajar.")
    initial_competencies: list[str] = Field(description="Kompetensi awal yang diharapkan sudah dimiliki peserta didik.")
    pancasila_profile: list[PancasilaDimension] = Field(description="2 sampai 3 dimensi Profil Pelajar Pancasila.")
    facilities: list[str] = Field(description="Sarana dan prasarana.")
    target_students: str = Field(description="Target peserta didik.")
    learning_model: LearningModel
    learning_objectives: list[SourcedItem] = Field(description="Tujuan Pembelajaran.")
    meaningful_understanding: list[str] = Field(description="Pemahaman bermakna.")
    trigger_questions: list[str] = Field(description="Pertanyaan pemantik.")
    preparation: list[str] = Field(description="Persiapan pembelajaran.")
    meetings: list[Meeting] = Field(description="Satu entri untuk setiap pertemuan.")
    assessment: Assessment
    enrichment: list[str] = Field(description="Kegiatan pengayaan.")
    remedial: list[str] = Field(description="Kegiatan remedial.")
    reflection: Reflection
    attachments: Attachments


class Identity(BaseModel):
    subject: str
    grade_level: str
    fase: str | None = None
    topic: str
    meetings: int
    minutes_per_meeting: int
    teaching_model: str


class Reference(BaseModel):
    id: str
    document_title: str
    page: int | None = None
    page_end: int | None = None
    heading: str | None = None


class ModulContent(GeneratedModul):
    """The stored form: generated content plus facts the server guarantees."""

    schema_version: Literal[2] = SCHEMA_VERSION
    identity: Identity
    references: list[Reference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
