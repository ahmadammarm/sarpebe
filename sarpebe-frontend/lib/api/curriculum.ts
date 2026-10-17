import { apiClient } from "./client";
import type { CurriculumUploadInput } from "@/lib/utils/validators";
import type { CurriculumDocument } from "@/types/curriculum";

export async function getCurriculumDocuments(): Promise<CurriculumDocument[]> {
  const res = await apiClient.get<CurriculumDocument[]>("/api/curriculum");
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

export async function deleteCurriculumDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/curriculum/${id}`);
}
