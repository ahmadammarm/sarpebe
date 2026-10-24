const FILENAME_MAX_STEM = 80;

/** Short Indonesian date, e.g. "25 Okt 2026". */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}

/** Short Indonesian date and time, e.g. "25 Okt, 15.30". */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

/** Canonical form of a class or subject label, as the backend stores it (`normalize_label`). */
export function normalizeLabel(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLowerCase();
}

/**
 * A download name that is valid on every operating system: ASCII letters, digits, dot, dash and
 * underscore, with accents folded to their base letter. Mirrors `safe_filename` in the backend.
 */
export function safeFilename(stem: string, extension: string, fallback = "Modul_Ajar"): string {
  const cleaned = stem
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^A-Za-z0-9._-]+/g, "_")
    .replace(/^[._-]+|[._-]+$/g, "")
    .slice(0, FILENAME_MAX_STEM)
    .replace(/[._-]+$/g, "");
  return `${cleaned || fallback}.${extension.replace(/^\./, "")}`;
}
