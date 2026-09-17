import { apiClient } from "./client";

export interface CurriculumDocument {
  id: string;
  title: string;
  document_type: string;
  url_path: string;
  status: "processing" | "completed" | "failed";
  uploaded_at: string;
}

export async function getCurriculumDocuments(): Promise<CurriculumDocument[]> {
  const res = await apiClient.get<CurriculumDocument[]>("/api/curriculum");
  return res.data;
}

export async function uploadCurriculumDocument(formData: FormData): Promise<CurriculumDocument> {
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
