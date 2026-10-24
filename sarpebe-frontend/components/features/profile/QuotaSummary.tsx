import { formatDateTime } from "@/lib/utils/formatters";
import type { Quota } from "@/types/user";

/** What the account may do now: how many modules are left, and when the next slot frees up. */
export function QuotaSummary({ quota }: { quota: Quota }) {
  if (quota.unlimited) {
    return <p className="text-ink-soft">Akun Anda tidak dibatasi dalam jumlah modul ajar yang bisa disusun.</p>;
  }

  return (
    <div className="space-y-1.5">
      <p>
        <span className="font-display text-3xl font-bold tabular-nums">{quota.remaining}</span>{" "}
        <span className="text-ink-soft">dari {quota.limit} modul tersisa dalam 24 jam terakhir.</span>
      </p>
      {quota.resets_at && (
        <p className="text-sm text-ink-soft">Satu slot kembali pada {formatDateTime(quota.resets_at)}.</p>
      )}
    </div>
  );
}
