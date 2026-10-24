const NO_CONTEXT_MARKER = "Belum ada dokumen kurikulum";
const NOT_COVERED_MARKER = "belum membahas topik ini";

export interface FailureDescription {
  message: string;
  /** What the user can do about it, when there is something. */
  hint?: string;
}

const NO_CONTEXT: FailureDescription = {
  message: "Belum ada dokumen kurikulum untuk kelas dan mata pelajaran ini.",
  hint: "Minta administrator mengunggah dokumen CP untuk kelas dan mata pelajaran tersebut, atau periksa penulisannya.",
};

const NOT_COVERED: FailureDescription = {
  message: "Dokumen kurikulum yang tersedia belum membahas topik ini.",
  hint: "Ubah topiknya agar sesuai dengan isi CP, atau minta administrator mengunggah dokumen yang memuatnya.",
};

const FAILURES_BY_CODE: Record<string, FailureDescription> = {
  llm_output_invalid: {
    message: "Modul yang disusun belum memenuhi format.",
    hint: "Coba buat ulang. Hasilnya bisa berbeda pada percobaan berikutnya.",
  },
  content_blocked: {
    message: "Modul untuk topik ini tidak dapat disusun.",
    hint: "Ubah rumusan topik atau catatan kelas, lalu coba lagi.",
  },
  llm_unavailable: {
    message: "Layanan penyusun modul sedang tidak tersedia.",
    hint: "Coba lagi beberapa saat lagi.",
  },
  timeout: {
    message: "Penyusunan modul melebihi batas waktu.",
    hint: "Coba buat ulang. Jika terus gagal, hubungi administrator.",
  },
};

const GENERIC: FailureDescription = {
  message: "Modul belum berhasil disusun.",
  hint: "Coba buat ulang. Jika terus gagal, hubungi administrator.",
};

/**
 * Turns the failure a plan stored into something a teacher can act on. The stable `code` decides;
 * the two curriculum-coverage texts are still recognised for plans saved before codes existed.
 * The backend's own text is never shown as is.
 */
export function describeFailure(error: string | null | undefined, code?: string | null): FailureDescription {
  if (error?.includes(NO_CONTEXT_MARKER)) return NO_CONTEXT;
  if (error?.includes(NOT_COVERED_MARKER)) return NOT_COVERED;
  if (code === "insufficient_context") return NOT_COVERED;
  return (code && FAILURES_BY_CODE[code]) || GENERIC;
}
