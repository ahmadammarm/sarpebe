"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteCurriculumDocument,
  getCurriculumDocuments,
  uploadCurriculumDocument,
} from "@/lib/api/curriculum";

const POLL_INTERVAL_MS = 3000;

export const curriculumKeys = {
  all: ["curriculum"] as const,
};

/** Admin document list; keeps refreshing while any document is still being indexed. */
export function useCurriculumDocuments(enabled = true) {
  return useQuery({
    queryKey: curriculumKeys.all,
    queryFn: getCurriculumDocuments,
    enabled,
    refetchInterval: (query) =>
      query.state.data?.some((doc) => doc.status === "processing") ? POLL_INTERVAL_MS : false,
  });
}

export function useUploadCurriculumDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadCurriculumDocument,
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
