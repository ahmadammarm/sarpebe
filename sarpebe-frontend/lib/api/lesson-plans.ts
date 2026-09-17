import { apiClient } from "./client";

export interface LessonPlan {
  id: string;
  grade_level: string;
  subject: string;
  topic: string;
  status: "pending" | "processing" | "completed" | "failed";
  generated_content?: {
    title?: string;
    objectives?: string[];
    materials?: string[];
    activities?: { duration: string; description: string }[];
    assessment?: string;
    citations?: string[];
    [key: string]: any;
  } | null;
  created_at: string;
}

export interface PaginatedLessonPlans {
  items: LessonPlan[];
  total: number;
  skip: number;
  limit: number;
}

export interface CreateLessonPlanPayload {
  grade_level: string;
  subject: string;
  topic: string;
}

export interface CreateLessonPlanResponse {
  job_id: string;
  id: string;
}

export async function createLessonPlan(payload: CreateLessonPlanPayload): Promise<CreateLessonPlanResponse> {
  const res = await apiClient.post<CreateLessonPlanResponse>("/api/lesson-plans", payload);
  return res.data;
}

export async function getLessonPlans(skip = 0, limit = 20): Promise<PaginatedLessonPlans> {
  const res = await apiClient.get<PaginatedLessonPlans>("/api/lesson-plans", {
    params: { skip, limit },
  });
  return res.data;
}

export async function getLessonPlan(id: string): Promise<LessonPlan> {
  const res = await apiClient.get<LessonPlan>(`/api/lesson-plans/${id}`);
  return res.data;
}

export async function updateLessonPlan(id: string, generatedContent: any): Promise<LessonPlan> {
  const res = await apiClient.put<LessonPlan>(`/api/lesson-plans/${id}`, {
    generated_content: generatedContent,
  });
  return res.data;
}

export async function deleteLessonPlan(id: string): Promise<void> {
  await apiClient.delete(`/api/lesson-plans/${id}`);
}

export async function downloadLessonPlanPdf(id: string, topicName = "Modul_Ajar"): Promise<void> {
  const response = await apiClient.get(`/api/lesson-plans/${id}/export/pdf`, {
    responseType: "blob",
  });

  const blob = new Blob([response.data], { type: "application/pdf" });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  const safeFilename = `${topicName.replace(/\s+/g, "_")}.pdf`;
  link.setAttribute("download", safeFilename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
}
