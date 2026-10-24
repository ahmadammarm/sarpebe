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
  ingest_version: number;
  /** Notes from reading the PDF; when `status` is "failed" it holds the reason. */
  ingest_warnings: string[] | null;
  uploaded_at: string;
}

export interface PaginatedCurriculumDocuments {
  items: CurriculumDocument[];
  total: number;
  skip: number;
  limit: number;
}
