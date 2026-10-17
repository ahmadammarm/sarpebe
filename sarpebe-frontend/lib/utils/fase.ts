export interface Fase {
  code: "A" | "B" | "C" | "D" | "E" | "F";
  /** Human-readable grade range, e.g. "kelas 7–9". */
  grades: string;
}

// Kurikulum Merdeka learning phases for SD/SMP/SMA (Fase Fondasi for PAUD is not covered).
const FASE_RANGES: { from: number; to: number; fase: Fase }[] = [
  { from: 1, to: 2, fase: { code: "A", grades: "kelas 1–2" } },
  { from: 3, to: 4, fase: { code: "B", grades: "kelas 3–4" } },
  { from: 5, to: 6, fase: { code: "C", grades: "kelas 5–6" } },
  { from: 7, to: 9, fase: { code: "D", grades: "kelas 7–9" } },
  { from: 10, to: 10, fase: { code: "E", grades: "kelas 10" } },
  { from: 11, to: 12, fase: { code: "F", grades: "kelas 11–12" } },
];

/** The Kurikulum Merdeka phase for a grade typed as a plain number, or null if it isn't one. */
export function faseForGrade(grade: string): Fase | null {
  const value = grade.trim();
  if (!/^\d{1,2}$/.test(value)) return null;

  const number = Number(value);
  return FASE_RANGES.find((range) => number >= range.from && number <= range.to)?.fase ?? null;
}
