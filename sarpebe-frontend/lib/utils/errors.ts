import axios from "axios";

// Backend error codes mapped to the wording shown to users. The backend's own `detail` text
// is for developers (English), so it is never displayed.
const MESSAGES_BY_CODE: Record<string, string> = {
  invalid_credentials: "Email atau password salah.",
  email_not_verified: "Email Anda belum diverifikasi.",
  too_many_attempts: "Terlalu banyak percobaan. Coba lagi beberapa menit lagi.",
  invalid_email_token: "Tautan ini tidak valid atau sudah kedaluwarsa. Minta tautan baru.",
  invalid_refresh_token: "Sesi Anda berakhir. Silakan masuk lagi.",
  invalid_token: "Sesi Anda berakhir. Silakan masuk lagi.",
  invalid_upload: "File tidak dapat diunggah. Pastikan berupa PDF yang valid dan tidak lebih dari 20 MB.",
  invalid_state: "Tindakan ini belum bisa dilakukan pada status modul saat ini.",
  lesson_plan_not_found: "Modul ajar tidak ditemukan.",
  document_not_found: "Dokumen tidak ditemukan.",
  not_owner: "Anda tidak punya akses ke data ini.",
};

/** The backend's stable machine-readable error code (e.g. "email_not_verified"), if any. */
export function getErrorCode(error: unknown): string | undefined {
  if (axios.isAxiosError(error)) {
    const code = error.response?.data?.code;
    if (typeof code === "string") return code;
  }
  return undefined;
}

/** User-facing message for an API error: a known code's wording, otherwise `fallback`. */
export function getErrorMessage(error: unknown, fallback: string): string {
  const code = getErrorCode(error);
  return (code && MESSAGES_BY_CODE[code]) || fallback;
}

export function isNotFoundError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}
