"use client";

import { Ban, CircleCheck, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { formatDate } from "@/lib/utils/formatters";
import type { AdminUser, AdminUserChanges, SubscriptionTier, UserRole } from "@/types/user";

interface UserTableProps {
  users: AdminUser[];
  currentUserId: string;
  /** The account a change or deletion is running for; its controls wait. */
  busyId: string | null;
  onChange: (user: AdminUser, changes: AdminUserChanges) => void;
  onDelete: (user: AdminUser) => void;
}

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "user", label: "Guru" },
  { value: "admin", label: "Administrator" },
];

const TIER_OPTIONS: { value: SubscriptionTier; label: string }[] = [
  { value: "free", label: "Gratis" },
  { value: "premium", label: "Premium" },
];

/** Accounts as rows that stack on a phone; each row carries its own controls. */
export function UserTable({ users, currentUserId, busyId, onChange, onDelete }: UserTableProps) {
  return (
    <ul className="divide-y divide-rule">
      {users.map((user, index) => {
        const isSelf = user.id === currentUserId;
        const disabled = user.disabled_at !== null;
        const busy = busyId === user.id;
        const name = user.full_name;

        return (
          <li
            key={user.id}
            className="row-in grid gap-4 py-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center lg:gap-6"
            style={{ "--delay": `${Math.min(index, 8) * 45}ms` } as React.CSSProperties}
          >
            <div className="min-w-0">
              <p className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="font-display text-lg font-semibold leading-snug [overflow-wrap:anywhere]">{name}</span>
                {isSelf && <span className="rounded-sm border border-rule px-1.5 py-0.5 text-xs font-semibold">Anda</span>}
                {disabled && (
                  <span className="inline-flex items-center gap-1.5 rounded-sm border border-margin/40 bg-margin-wash px-2 py-0.5 text-xs font-semibold text-margin-text">
                    <Ban className="size-3.5" aria-hidden />
                    Dinonaktifkan
                  </span>
                )}
              </p>
              <p className="mt-0.5 text-sm text-ink-soft [overflow-wrap:anywhere]">{user.email ?? "Tanpa email"}</p>
              <p className="mt-0.5 text-sm text-ink-soft">
                Bergabung <time dateTime={user.created_at}>{formatDate(user.created_at)}</time>
                {user.school_name ? ` · ${user.school_name}` : ""}
                {user.email_verified_at === null ? " · Email belum diverifikasi" : ""}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Select
                aria-label={`Peran ${name}`}
                value={user.role}
                disabled={isSelf || busy}
                onChange={(e) => onChange(user, { role: e.target.value as UserRole })}
                className="w-auto min-w-36"
              >
                {ROLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
              <Select
                aria-label={`Paket ${name}`}
                value={user.subscription_tier}
                disabled={busy}
                onChange={(e) => onChange(user, { subscription_tier: e.target.value as SubscriptionTier })}
                className="w-auto min-w-28"
              >
                {TIER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
              <Button
                variant="ghost"
                size="sm"
                disabled={isSelf || busy}
                onClick={() => onChange(user, { disabled: !disabled })}
                aria-label={`${disabled ? "Aktifkan" : "Nonaktifkan"} akun ${name}`}
              >
                {disabled ? <CircleCheck aria-hidden /> : <Ban aria-hidden />}
                {disabled ? "Aktifkan" : "Nonaktifkan"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                disabled={isSelf || busy}
                onClick={() => onDelete(user)}
                aria-label={`Hapus akun ${name}`}
                className="text-ink-soft hover:bg-margin-wash hover:text-margin-text"
              >
                <Trash2 aria-hidden />
                Hapus
              </Button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
