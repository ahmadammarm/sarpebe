import type { CurriculumDocument, DocumentType } from "@/types/curriculum";

export const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "CP", label: "Capaian Pembelajaran (CP)" },
  { value: "ATP", label: "Alur Tujuan Pembelajaran (ATP)" },
  { value: "BUKU_GURU", label: "Buku Guru" },
];

export const DOCUMENT_TYPE_LABELS: Record<CurriculumDocument["document_type"], string> = {
  CP: "Capaian Pembelajaran",
  ATP: "Alur Tujuan Pembelajaran",
  BUKU_GURU: "Buku Guru",
};
