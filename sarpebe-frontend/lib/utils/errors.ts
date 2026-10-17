import axios from "axios";

/** Extracts the backend's `detail` message (string details only) or falls back to a default. */
export function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail) return detail;
  }
  return fallback;
}

/** The backend's stable machine-readable error code (e.g. "email_not_verified"), if any. */
export function getErrorCode(error: unknown): string | undefined {
  if (axios.isAxiosError(error)) {
    const code = error.response?.data?.code;
    if (typeof code === "string") return code;
  }
  return undefined;
}

export function isNotFoundError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}
