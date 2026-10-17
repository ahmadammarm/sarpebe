"use client";

import { useEffect, useState } from "react";
import { getJobStatus, streamJobStatus } from "@/lib/api/lesson-plans";
import { isNotFoundError } from "@/lib/utils/errors";
import type { JobStatus, LessonPlanStatus } from "@/types/lesson-plan";

const INITIAL_POLL_DELAY_MS = 1500;
const MAX_POLL_DELAY_MS = 8000;

function isTerminal(status: LessonPlanStatus): boolean {
  return status === "completed" || status === "failed";
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener("abort", () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

/**
 * Follows a generation job: streams authenticated SSE updates, and if the stream fails or
 * closes early, falls back to polling the status endpoint with exponential backoff.
 */
interface JobState {
  jobId: string;
  job: JobStatus | null;
  connectionError: string | null;
}

export function useJobStatus(jobId: string | null) {
  // Tagged with the job it belongs to, so switching jobs never shows stale state.
  const [state, setState] = useState<JobState | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const controller = new AbortController();
    const { signal } = controller;

    const update = (patch: Partial<Omit<JobState, "jobId">>) => {
      if (signal.aborted) return;
      setState((prev) => ({
        jobId,
        job: null,
        connectionError: null,
        ...(prev?.jobId === jobId ? prev : {}),
        ...patch,
      }));
    };

    const apply = (next: JobStatus): boolean => {
      if (signal.aborted) return true;
      update({ job: next });
      return isTerminal(next.status);
    };

    async function follow(id: string) {
      try {
        if (await streamJobStatus(id, apply, signal)) return;
      } catch {
        if (signal.aborted) return;
      }

      let delay = INITIAL_POLL_DELAY_MS;
      while (!signal.aborted) {
        try {
          if (apply(await getJobStatus(id))) return;
          update({ connectionError: null });
        } catch (err) {
          if (isNotFoundError(err)) {
            apply({ job_id: id, status: "failed", lesson_plan_id: null, error: "Pekerjaan tidak ditemukan." });
            return;
          }
          update({ connectionError: "Gagal memperbarui status pekerjaan. Mencoba lagi..." });
        }
        await sleep(delay, signal);
        delay = Math.min(delay * 1.5, MAX_POLL_DELAY_MS);
      }
    }

    void follow(jobId);

    return () => controller.abort();
  }, [jobId]);

  const current = jobId && state?.jobId === jobId ? state : null;
  const job = current?.job ?? null;
  const status: LessonPlanStatus = job?.status ?? "pending";
  return {
    status,
    isDone: isTerminal(status),
    lessonPlanId: job?.lesson_plan_id ?? null,
    error: job?.error ?? current?.connectionError ?? null,
  };
}
