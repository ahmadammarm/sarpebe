"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteCurriculumDocument,
  getCurriculumDocuments,
  reindexCurriculumDocument,
  updateCurriculumDocument,
  uploadCurriculumDocument,
} from "@/lib/api/curriculum";
import type { CurriculumEditInput } from "@/lib/utils/validators";

const POLL_INTERVAL_MS = 3000;

export const curriculumKeys = {
  all: ["curriculum"] as const,
  list: (skip: number, limit: number) => ["curriculum", skip, limit] as const,
};

/** One page of the admin document list; keeps refreshing while any document on it is still being indexed. */
export function useCurriculumDocuments(skip: number, limit: number, enabled = true) {
  return useQuery({
    queryKey: curriculumKeys.list(skip, limit),
    queryFn: () => getCurriculumDocuments(skip, limit),
    enabled,
    placeholderData: keepPreviousData,
    refetchInterval: (query) =>
      query.state.data?.items.some((doc) => doc.status === "processing") ? POLL_INTERVAL_MS : false,
  });
}

export function useUploadCurriculumDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadCurriculumDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: curriculumKeys.all }),
  });
}

export function useUpdateCurriculumDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, changes }: { id: string; changes: Partial<CurriculumEditInput> }) =>
      updateCurriculumDocument(id, changes),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: curriculumKeys.all }),
  });
}

export function useReindexCurriculumDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: reindexCurriculumDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: curriculumKeys.all }),
  });
}

export function useDeleteCurriculumDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCurriculumDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: curriculumKeys.all }),
  });
}
