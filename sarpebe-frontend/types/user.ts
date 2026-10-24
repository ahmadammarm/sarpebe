/** How many lesson plans a user can still start in the last 24 hours (mirrors `QuotaResponse`). */
export interface Quota {
  /** null when the user is not limited. */
  limit: number | null;
  used: number;
  /** null when the user is not limited. */
  remaining: number | null;
  unlimited: boolean;
  /** When the oldest counted plan leaves the window and a slot frees up; null if none is counted. */
  resets_at: string | null;
}

export type UserRole = "user" | "admin";
export type SubscriptionTier = "free" | "premium";

/** The signed-in user's own details (mirrors `ProfileResponse`). */
export interface Profile {
  id: string;
  email: string | null;
  full_name: string;
  school_name: string | null;
  subscription_tier: string;
  role: string;
  created_at: string;
}

/** An account as an administrator sees it (mirrors `AdminUserResponse`). */
export interface AdminUser extends Profile {
  email_verified_at: string | null;
  /** null while the account is active. */
  disabled_at: string | null;
}

export interface PaginatedUsers {
  items: AdminUser[];
  total: number;
  skip: number;
  limit: number;
}

/** What an administrator can change on another account (mirrors `UserAdminUpdate`). */
export interface AdminUserChanges {
  role?: UserRole;
  subscription_tier?: SubscriptionTier;
  disabled?: boolean;
}
