import { z } from "zod";

const MAX_PASSWORD_BYTES = 72; // bcrypt's limit, enforced by the backend as well

// Strength rules for choosing a password. Login deliberately does not apply them:
// accounts imported from the old auth provider may have shorter passwords.
const newPasswordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters.")
  .refine((value) => new TextEncoder().encode(value).length <= MAX_PASSWORD_BYTES, "Password is too long.");

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});

export const registerSchema = z.object({
  fullName: z.string().trim().min(2, "Full name must be at least 2 characters."),
  email: z.string().email("Please enter a valid email address."),
  password: newPasswordSchema,
});

export const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
});

export const resetPasswordSchema = z
  .object({
    password: newPasswordSchema,
    confirmPassword: z.string(),
  })
  .refine((value) => value.password === value.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match.",
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
export type RegisterInput = RegisterFormData;
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;
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
