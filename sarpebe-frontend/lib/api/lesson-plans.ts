import { apiClient } from "./client";

export interface LessonPlan {
  id: string;
  grade_level: string;
  subject: string;
  topic: string;
  status: "pending" | "completed" | "failed";
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

export function getLessonPlanPdfExportUrl(id: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  return `${baseUrl}/api/lesson-plans/${id}/export/pdf`;
}
