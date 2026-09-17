"use client";

import { useEffect, useState } from "react";

export function useJobSSE(jobId: string | null) {
  const [status, setStatus] = useState<string>("pending");
  const [isDone, setIsDone] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const eventSource = new EventSource(`${baseUrl}/api/lesson-plans/jobs/${jobId}/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setStatus(data.status);
        if (data.status === "completed" || data.status === "failed") {
          setIsDone(true);
          eventSource.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE event", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE stream error:", err);
      setError("Error connecting to real-time update stream.");
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  return { status, isDone, error };
}
