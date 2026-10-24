export type LessonPlanStatus = "pending" | "processing" | "completed" | "failed";

/** Real steps of a running job, reported by the backend while status is "processing". */
export type GenerationStage = "retrieving" | "drafting" | "repairing";

export const TEACHING_MODELS = [
  { value: "otomatis", label: "Biarkan sistem memilih" },
  { value: "diskusi_kelompok", label: "Diskusi kelompok" },
  { value: "pjbl", label: "Project Based Learning (PjBL)" },
  { value: "pbl", label: "Problem Based Learning (PBL)" },
  { value: "inkuiri", label: "Inkuiri" },
  { value: "kooperatif", label: "Pembelajaran kooperatif" },
  { value: "ceramah_interaktif", label: "Ceramah interaktif" },
] as const;

export type TeachingModel = (typeof TEACHING_MODELS)[number]["value"];

/** Options the teacher chose when the plan was created. */
export interface RequestOptions {
  meeting_count?: number;
  minutes_per_meeting?: number;
  teaching_model?: TeachingModel;
  class_notes?: string | null;
}

// ---------------------------------------------------------------------------
// schema_version 1: the original short format. Kept so older plans still open.
// ---------------------------------------------------------------------------

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
  /** Stable failure identifier stored next to `error`. */
  code?: string;
  raw?: string;
}

// ---------------------------------------------------------------------------
// schema_version 2: full Modul Ajar. Mirrors app/schemas/lesson_plan_content.py.
// ---------------------------------------------------------------------------

export interface Table {
  caption: string;
  columns: string[];
  rows: string[][];
}

export interface SourcedItem {
  text: string;
  source_ids: string[];
  grounded: boolean;
}

export type PancasilaDimensionName =
  | "Beriman dan Bertakwa"
  | "Berkebinekaan Global"
  | "Bergotong Royong"
  | "Mandiri"
  | "Bernalar Kritis"
  | "Kreatif";

export interface PancasilaDimension {
  dimension: PancasilaDimensionName;
  how: string;
}

export interface Meeting {
  number: number;
  title: string;
  activities: Table;
}

export interface AssessmentItem {
  technique: string;
  instrument: string;
  description: string;
}

export interface Assessment {
  diagnostic: AssessmentItem;
  formative: AssessmentItem;
  summative: AssessmentItem;
  overview: Table;
  rubric: Table;
}

export interface Worksheet {
  title: string;
  instructions: string;
  tasks: string[];
}

export interface GlossaryItem {
  term: string;
  definition: string;
}

export interface Attachments {
  worksheet: Worksheet;
  reading_material: string;
  glossary: GlossaryItem[];
}

export interface Identity {
  subject: string;
  grade_level: string;
  fase: string | null;
  topic: string;
  meetings: number;
  minutes_per_meeting: number;
  teaching_model: string;
}

export interface Reference {
  id: string;
  document_title: string;
  page: number | null;
  page_end: number | null;
  heading: string | null;
}

export interface LessonPlanContentV2 {
  schema_version: 2;
  insufficient_context: boolean;
  insufficient_reason: string;
  title: string;
  initial_competencies: string[];
  pancasila_profile: PancasilaDimension[];
  facilities: string[];
  target_students: string;
  learning_model: { name: string; rationale: string };
  learning_objectives: SourcedItem[];
  meaningful_understanding: string[];
  trigger_questions: string[];
  preparation: string[];
  meetings: Meeting[];
  assessment: Assessment;
  enrichment: string[];
  remedial: string[];
  reflection: { teacher: string[]; students: string[] };
  attachments: Attachments;
  identity: Identity;
  references: Reference[];
  warnings: string[];
  /** Present only on failed plans, where the stored content is an error record. */
  error?: string;
  /** Stable failure identifier stored next to `error`. */
  code?: string;
}

interface LessonPlanBase {
  id: string;
  grade_level: string;
  subject: string;
  topic: string;
  status: LessonPlanStatus;
  request_options: RequestOptions | null;
  created_at: string;
}

export interface LessonPlanV1 extends LessonPlanBase {
  schema_version: 1;
  generated_content: LessonPlanContent | null;
}

export interface LessonPlanV2 extends LessonPlanBase {
  schema_version: 2;
  generated_content: LessonPlanContentV2 | null;
}

export type LessonPlan = LessonPlanV1 | LessonPlanV2;

/** Content as stored on a plan that has not completed: only the failure text matters. */
export type AnyLessonPlanContent = LessonPlanContent | LessonPlanContentV2;

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
  stage: GenerationStage | null;
  lesson_plan_id: string | null;
  error: string | null;
  error_code: string | null;
}
