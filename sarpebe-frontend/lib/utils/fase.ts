export interface Fase {
  code: "A" | "B" | "C" | "D" | "E" | "F";
  /** Human-readable grade range, e.g. "kelas 7–9". */
  grades: string;
  /** School level the phase belongs to. */
  level: "SD" | "SMP" | "SMA";
  from: number;
  to: number;
}

// Kurikulum Merdeka learning phases for SD/SMP/SMA (Fase Fondasi for PAUD is not covered).
export const FASES: readonly Fase[] = [
  { code: "A", grades: "kelas 1–2", level: "SD", from: 1, to: 2 },
  { code: "B", grades: "kelas 3–4", level: "SD", from: 3, to: 4 },
  { code: "C", grades: "kelas 5–6", level: "SD", from: 5, to: 6 },
  { code: "D", grades: "kelas 7–9", level: "SMP", from: 7, to: 9 },
  { code: "E", grades: "kelas 10", level: "SMA", from: 10, to: 10 },
  { code: "F", grades: "kelas 11–12", level: "SMA", from: 11, to: 12 },
];

/** The Kurikulum Merdeka phase for a grade typed as a plain number, or null if it isn't one. */
export function faseForGrade(grade: string): Fase | null {
  const value = grade.trim();
  if (!/^\d{1,2}$/.test(value)) return null;

  const number = Number(value);
  return FASES.find((fase) => number >= fase.from && number <= fase.to) ?? null;
}
