from dataclasses import dataclass


@dataclass(frozen=True)
class Fase:
    code: str  # "A" .. "F"
    grades: str  # e.g. "kelas 7-9"
    level: str  # "SD" | "SMP" | "SMA"
    from_grade: int
    to_grade: int


# Kurikulum Merdeka learning phases for SD/SMP/SMA. Mirrors sarpebe-frontend/lib/utils/fase.ts.
FASES: tuple[Fase, ...] = (
    Fase("A", "kelas 1-2", "SD", 1, 2),
    Fase("B", "kelas 3-4", "SD", 3, 4),
    Fase("C", "kelas 5-6", "SD", 5, 6),
    Fase("D", "kelas 7-9", "SMP", 7, 9),
    Fase("E", "kelas 10", "SMA", 10, 10),
    Fase("F", "kelas 11-12", "SMA", 11, 12),
)


def fase_for_grade(grade: str) -> Fase | None:
    """The phase for a grade written as a plain number (1-12), or None for any other text."""
    value = grade.strip()
    if not value.isascii() or not value.isdigit() or len(value) > 2:
        return None
    number = int(value)
    return next((fase for fase in FASES if fase.from_grade <= number <= fase.to_grade), None)
