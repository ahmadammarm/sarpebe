export type LessonPlanStatus = "pending" | "processing" | "completed" | "failed";

export interface LessonActivity {
  duration: string;
  description: string;
}

export interface LessonPlanContent {
  title?: string;
  objectives?: string[];
  materials?: string[];
  activities?: LessonActivity[];
  assessment?: string;
  citations?: string[];
  /** Present when generation failed. */
  error?: string;
  raw?: string;
}

export interface LessonPlan {
  id: string;
  grade_level: string;
  subject: string;
  topic: string;
  status: LessonPlanStatus;
  generated_content: LessonPlanContent | null;
  created_at: string;
}

export interface PaginatedLessonPlans {
  items: LessonPlan[];
  total: number;
  skip: number;
  limit: number;
}

export interface CreateLessonPlanResponse {
  job_id: string;
  id: string;
}

export interface JobStatus {
  job_id: string;
  status: LessonPlanStatus;
  lesson_plan_id: string | null;
  error: string | null;
}
