"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import {
  changePassword,
  deleteMyAccount,
  deleteUser,
  getMe,
  getMyQuota,
  getUsers,
  updateMe,
  updateUser,
  type UserListParams,
} from "@/lib/api/users";
import type { ChangePasswordInput } from "@/lib/utils/validators";
import type { AdminUserChanges } from "@/types/user";

export const userKeys = {
  all: ["users"] as const,
  quota: ["users", "quota"] as const,
  profile: ["users", "me"] as const,
  list: (params: UserListParams) => ["users", "list", params] as const,
  lists: ["users", "list"] as const,
};

/** Lesson plans the signed-in user can still start; refetched after every plan is created. */
export function useQuota(enabled = true) {
  return useQuery({
    queryKey: userKeys.quota,
    queryFn: getMyQuota,
    enabled,
  });
}

/** The signed-in user's own details. */
export function useProfile(enabled = true) {
  return useQuery({
    queryKey: userKeys.profile,
    queryFn: getMe,
    enabled,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const { update } = useSession();
  return useMutation({
    mutationFn: updateMe,
    onSuccess: async (profile) => {
      queryClient.setQueryData(userKeys.profile, profile);
      // The header shows the name from the session, so it needs the new one too.
      await update({ name: profile.full_name });
    },
  });
}

/** On success the backend has signed this user out everywhere; the caller then signs out and goes to the login page. */
export function useChangePassword() {
  return useMutation({
    mutationFn: ({ current_password, new_password }: Pick<ChangePasswordInput, "current_password" | "new_password">) =>
      changePassword(current_password, new_password),
  });
}

export function useDeleteAccount() {
  return useMutation({ mutationFn: deleteMyAccount });
}

/** One page of the administrator's user list. */
export function useAdminUsers(params: UserListParams, enabled = true) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => getUsers(params),
    enabled,
    placeholderData: keepPreviousData,
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, changes }: { id: string; changes: AdminUserChanges }) => updateUser(id, changes),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.lists }),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.lists }),
  });
}
