import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(6, "Password must be at least 6 characters."),
});

export const registerSchema = z.object({
  fullName: z.string().min(2, "Full name must be at least 2 characters."),
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(6, "Password must be at least 6 characters."),
});

export const lessonPlanCreateSchema = z.object({
  grade_level: z
    .string()
    .trim()
    .min(1, "Tingkat kelas wajib diisi.")
    .max(20, "Tingkat kelas maksimal 20 karakter."),
  subject: z
    .string()
    .trim()
    .min(1, "Mata pelajaran wajib diisi.")
    .max(100, "Mata pelajaran maksimal 100 karakter."),
  topic: z
    .string()
    .trim()
    .min(1, "Topik wajib diisi.")
    .max(300, "Topik maksimal 300 karakter."),
});

export const MAX_UPLOAD_MB = 20;

export const curriculumUploadSchema = z.object({
  grade_level: lessonPlanCreateSchema.shape.grade_level,
  subject: lessonPlanCreateSchema.shape.subject,
  document_type: z.enum(["CP", "ATP", "BUKU_GURU"]),
  file: z
    .instanceof(File, { message: "File PDF wajib dipilih." })
    .refine((file) => file.name.toLowerCase().endsWith(".pdf"), "Hanya file PDF yang didukung.")
    .refine((file) => file.size <= MAX_UPLOAD_MB * 1024 * 1024, `Ukuran file maksimal ${MAX_UPLOAD_MB} MB.`),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type LessonPlanCreateInput = z.infer<typeof lessonPlanCreateSchema>;
export type CurriculumUploadInput = z.infer<typeof curriculumUploadSchema>;

/** Maps a ZodError to `{ field: firstMessage }` for inline form errors. */
export function zodFieldErrors<T extends string>(error: z.ZodError): Partial<Record<T, string>> {
  const fieldErrors: Partial<Record<T, string>> = {};
  for (const issue of error.issues) {
    const field = issue.path[0] as T | undefined;
    if (field !== undefined && !(field in fieldErrors)) {
      fieldErrors[field] = issue.message;
    }
  }
  return fieldErrors;
}
