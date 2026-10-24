import { apiClient } from "./client";
import type { CurriculumEditInput, CurriculumUploadInput } from "@/lib/utils/validators";
import type { CurriculumDocument, PaginatedCurriculumDocuments } from "@/types/curriculum";

export async function getCurriculumDocuments(skip = 0, limit = 20): Promise<PaginatedCurriculumDocuments> {
  const res = await apiClient.get<PaginatedCurriculumDocuments>("/api/curriculum", {
    params: { skip, limit },
  });
  return res.data;
}

export async function uploadCurriculumDocument(input: CurriculumUploadInput): Promise<CurriculumDocument> {
  const formData = new FormData();
  formData.append("file", input.file);
  formData.append("grade_level", input.grade_level);
  formData.append("subject", input.subject);
  formData.append("document_type", input.document_type);

  const res = await apiClient.post<CurriculumDocument>("/api/curriculum/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return res.data;
}

/** Sends only the fields that changed. A new class or subject makes the backend process the document again. */
export async function updateCurriculumDocument(
  id: string,
  changes: Partial<CurriculumEditInput>
): Promise<CurriculumDocument> {
  const res = await apiClient.patch<CurriculumDocument>(`/api/curriculum/${id}`, changes);
  return res.data;
}

export async function reindexCurriculumDocument(id: string): Promise<CurriculumDocument> {
  const res = await apiClient.post<CurriculumDocument>(`/api/curriculum/${id}/reindex`);
  return res.data;
}

export async function deleteCurriculumDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/curriculum/${id}`);
}
