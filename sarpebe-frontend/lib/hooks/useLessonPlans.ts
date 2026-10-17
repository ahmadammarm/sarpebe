"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createLessonPlan,
  deleteLessonPlan,
  downloadLessonPlanPdf,
  getLessonPlan,
  getLessonPlans,
  updateLessonPlan,
} from "@/lib/api/lesson-plans";
import type { AnyLessonPlanContent, LessonPlan, LessonPlanStatus } from "@/types/lesson-plan";

const POLL_INTERVAL_MS = 3000;

export const lessonPlanKeys = {
  all: ["lesson-plans"] as const,
  list: (skip: number, limit: number) => [...lessonPlanKeys.all, "list", skip, limit] as const,
  detail: (id: string) => [...lessonPlanKeys.all, "detail", id] as const,
};

export function isUnfinished(status: LessonPlanStatus): boolean {
  return status === "pending" || status === "processing";
}

/** Paginated list of the current user's plans; keeps refreshing while any plan is still generating. */
export function useLessonPlans(skip = 0, limit = 20, enabled = true) {
  return useQuery({
    queryKey: lessonPlanKeys.list(skip, limit),
    queryFn: () => getLessonPlans(skip, limit),
    enabled,
    refetchInterval: (query) =>
      query.state.data?.items.some((plan) => isUnfinished(plan.status)) ? POLL_INTERVAL_MS : false,
  });
}

/** A single plan; keeps refreshing until generation reaches a terminal status. */
export function useLessonPlan(id: string) {
  return useQuery({
    queryKey: lessonPlanKeys.detail(id),
    queryFn: () => getLessonPlan(id),
    enabled: Boolean(id),
    retry: false,
    refetchInterval: (query) => {
      const plan = query.state.data;
      return plan && isUnfinished(plan.status) ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useCreateLessonPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createLessonPlan,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: lessonPlanKeys.all }),
  });
}

export function useUpdateLessonPlan(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: AnyLessonPlanContent) => updateLessonPlan(id, content),
    onSuccess: (updated: LessonPlan) => {
      queryClient.setQueryData(lessonPlanKeys.detail(id), updated);
      queryClient.invalidateQueries({ queryKey: [...lessonPlanKeys.all, "list"] });
    },
  });
}

export function useDeleteLessonPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteLessonPlan,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: lessonPlanKeys.all }),
  });
}

export function useDownloadLessonPlanPdf() {
  return useMutation({
    mutationFn: ({ id, topic }: { id: string; topic: string }) => downloadLessonPlanPdf(id, topic),
  });
}
