import { apiClient } from "./client";
import type { ProfileInput } from "@/lib/utils/validators";
import type { AdminUser, AdminUserChanges, PaginatedUsers, Profile, Quota, UserRole } from "@/types/user";

export async function getMe(): Promise<Profile> {
  const res = await apiClient.get<Profile>("/api/users/me");
  return res.data;
}

export async function getMyQuota(): Promise<Quota> {
  const res = await apiClient.get<Quota>("/api/users/me/quota");
  return res.data;
}

export async function updateMe(input: ProfileInput): Promise<Profile> {
  const res = await apiClient.patch<Profile>("/api/users/me", input);
  return res.data;
}

/** Signs the user out of every device on success, so the caller must sign in again afterwards. */
export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await apiClient.post("/api/users/me/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export async function deleteMyAccount(password: string): Promise<void> {
  await apiClient.delete("/api/users/me", { data: { password } });
}

export interface UserListParams {
  skip: number;
  limit: number;
  q?: string;
  role?: UserRole;
}

export async function getUsers({ skip, limit, q, role }: UserListParams): Promise<PaginatedUsers> {
  const res = await apiClient.get<PaginatedUsers>("/api/users", {
    params: { skip, limit, q: q || undefined, role },
  });
  return res.data;
}

export async function updateUser(id: string, changes: AdminUserChanges): Promise<AdminUser> {
  const res = await apiClient.patch<AdminUser>(`/api/users/${id}`, changes);
  return res.data;
}

export async function deleteUser(id: string): Promise<void> {
  await apiClient.delete(`/api/users/${id}`);
}
