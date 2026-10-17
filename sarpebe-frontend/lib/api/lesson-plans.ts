import { API_BASE_URL, apiClient, getAuthToken } from "./client";
import type { LessonPlanCreateInput } from "@/lib/utils/validators";
import type {
  CreateLessonPlanResponse,
  JobStatus,
  LessonPlan,
  LessonPlanContent,
  PaginatedLessonPlans,
} from "@/types/lesson-plan";

export async function createLessonPlan(payload: LessonPlanCreateInput): Promise<CreateLessonPlanResponse> {
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

export async function updateLessonPlan(id: string, generatedContent: LessonPlanContent): Promise<LessonPlan> {
  const res = await apiClient.put<LessonPlan>(`/api/lesson-plans/${id}`, {
    generated_content: generatedContent,
  });
  return res.data;
}

export async function deleteLessonPlan(id: string): Promise<void> {
  await apiClient.delete(`/api/lesson-plans/${id}`);
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await apiClient.get<JobStatus>(`/api/lesson-plans/jobs/${jobId}`);
  return res.data;
}

/**
 * Follows a job over Server-Sent Events. EventSource cannot send an Authorization header and
 * axios cannot stream in the browser, so this is the one place that uses fetch directly.
 *
 * Calls `onEvent` for every status update; if it returns true the stream is closed.
 * Resolves true when a terminal status was seen, false if the server closed the stream early.
 * Rejects on HTTP/network errors so the caller can fall back to polling.
 */
export async function streamJobStatus(
  jobId: string,
  onEvent: (job: JobStatus) => boolean,
  signal: AbortSignal
): Promise<boolean> {
  const token = await getAuthToken();
  const res = await fetch(`${API_BASE_URL}/api/lesson-plans/jobs/${jobId}/stream`, {
    headers: {
      Accept: "text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Job stream failed with status ${res.status}`);
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) return false;

      buffer += value;
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
        if (!dataLine) continue;
        if (onEvent(JSON.parse(dataLine.slice("data: ".length)) as JobStatus)) return true;
      }
    }
  } finally {
    await reader.cancel().catch(() => undefined);
  }
}

export async function downloadLessonPlanPdf(id: string, topicName = "Modul_Ajar"): Promise<void> {
  const response = await apiClient.get<Blob>(`/api/lesson-plans/${id}/export/pdf`, {
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
