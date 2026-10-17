const NO_CONTEXT_MARKER = "Belum ada dokumen kurikulum";
const CRASH_MARKER = "Task crashed";

export interface FailureDescription {
  message: string;
  /** What the user can do about it, when there is something. */
  hint?: string;
}

/**
 * Turns the failure text the backend stores on a plan into something a teacher can act on.
 * Technical crash messages are replaced with a plain one; the original stays in the logs.
 */
export function describeFailure(error: string | null | undefined): FailureDescription {
  if (error?.includes(NO_CONTEXT_MARKER)) {
    return {
      message: "Belum ada dokumen kurikulum untuk kelas dan mata pelajaran ini.",
      hint: "Minta administrator mengunggah dokumen CP untuk kelas dan mata pelajaran tersebut, atau periksa penulisannya.",
    };
  }

  if (!error || error.includes(CRASH_MARKER)) {
    return {
      message: "Modul belum berhasil disusun.",
      hint: "Coba buat ulang. Jika terus gagal, hubungi administrator.",
    };
  }

  return { message: error };
}
