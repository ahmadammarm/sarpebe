import { z } from "zod";

const MAX_PASSWORD_BYTES = 72; // bcrypt's limit, enforced by the backend as well

// Strength rules for choosing a password. Login deliberately does not apply them:
// accounts imported from the old auth provider may have shorter passwords.
export const newPasswordSchema = z
  .string()
  .min(8, "Password minimal 8 karakter.")
  .refine((value) => new TextEncoder().encode(value).length <= MAX_PASSWORD_BYTES, "Password terlalu panjang.");

export const loginSchema = z.object({
  email: z.string().email("Masukkan alamat email yang valid."),
  password: z.string().min(1, "Password wajib diisi."),
});

export const registerSchema = z.object({
  fullName: z.string().trim().min(2, "Nama lengkap minimal 2 karakter."),
  email: z.string().email("Masukkan alamat email yang valid."),
  password: newPasswordSchema,
});

export const forgotPasswordSchema = z.object({
  email: z.string().email("Masukkan alamat email yang valid."),
});

export const resetPasswordSchema = z
  .object({
    password: newPasswordSchema,
    confirmPassword: z.string(),
  })
  .refine((value) => value.password === value.confirmPassword, {
    path: ["confirmPassword"],
    message: "Password tidak sama.",
  });

export const profileSchema = z.object({
  full_name: z.string().trim().min(2, "Nama lengkap minimal 2 karakter.").max(100, "Nama lengkap maksimal 100 karakter."),
  school_name: z.string().trim().max(150, "Nama sekolah maksimal 150 karakter."),
});

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Password saat ini wajib diisi."),
    new_password: newPasswordSchema,
    confirm_password: z.string(),
  })
  .refine((value) => value.new_password === value.confirm_password, {
    path: ["confirm_password"],
    message: "Password tidak sama.",
  });

export const deleteAccountSchema = z.object({
  password: z.string().min(1, "Masukkan password Anda untuk melanjutkan."),
});

export const MAX_CLASS_NOTES = 500;

const TEACHING_MODEL_VALUES = [
  "otomatis",
  "diskusi_kelompok",
  "pjbl",
  "pbl",
  "inkuiri",
  "kooperatif",
  "ceramah_interaktif",
] as const;

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
  meeting_count: z
    .number({ message: "Jumlah pertemuan harus berupa angka." })
    .int("Jumlah pertemuan harus bilangan bulat.")
    .min(1, "Minimal 1 pertemuan.")
    .max(6, "Maksimal 6 pertemuan."),
  minutes_per_meeting: z
    .number({ message: "Menit per pertemuan harus berupa angka." })
    .int("Menit per pertemuan harus bilangan bulat.")
    .min(20, "Minimal 20 menit.")
    .max(240, "Maksimal 240 menit."),
  teaching_model: z.enum(TEACHING_MODEL_VALUES),
  class_notes: z
    .string()
    .trim()
    .max(MAX_CLASS_NOTES, `Catatan maksimal ${MAX_CLASS_NOTES} karakter.`),
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

export const curriculumEditSchema = z.object({
  title: z.string().trim().min(1, "Judul wajib diisi.").max(255, "Judul maksimal 255 karakter."),
  document_type: z.enum(["CP", "ATP", "BUKU_GURU"]),
  grade_level: lessonPlanCreateSchema.shape.grade_level,
  subject: lessonPlanCreateSchema.shape.subject,
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type RegisterInput = RegisterFormData;
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;
export type LessonPlanCreateInput = z.infer<typeof lessonPlanCreateSchema>;
export type CurriculumUploadInput = z.infer<typeof curriculumUploadSchema>;
export type CurriculumEditInput = z.infer<typeof curriculumEditSchema>;
export type ProfileInput = z.infer<typeof profileSchema>;
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
export type DeleteAccountInput = z.infer<typeof deleteAccountSchema>;

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
