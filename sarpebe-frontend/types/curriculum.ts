export type DocumentType = "CP" | "ATP" | "BUKU_GURU";

export type CurriculumDocumentStatus = "processing" | "completed" | "failed";

export interface CurriculumDocument {
  id: string;
  title: string;
  document_type: DocumentType;
  url_path: string;
  grade_level: string | null;
  subject: string | null;
  status: CurriculumDocumentStatus;
  uploaded_at: string;
}
