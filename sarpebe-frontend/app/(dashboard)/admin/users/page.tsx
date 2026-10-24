"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { Search } from "lucide-react";
import { Sheet } from "@/components/brand/Sheet";
import { UserTable } from "@/components/features/admin/UserTable";
import { buttonVariants } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Notice } from "@/components/ui/notice";
import { Pagination } from "@/components/ui/pagination";
import { Select } from "@/components/ui/select";
import { useAdminUsers, useDeleteUser, useUpdateUser } from "@/lib/hooks/useUsers";
import { getErrorMessage } from "@/lib/utils/errors";
import type { AdminUser, AdminUserChanges, UserRole } from "@/types/user";

const PAGE_SIZE = 10;
const SEARCH_DELAY_MS = 300;

export default function AdminUsersPage() {
  const { data: session, status } = useSession();
  const isAdmin = status === "authenticated" && session?.user.role === "admin";

  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [role, setRole] = useState<UserRole | "">("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<AdminUser | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Search only after the typing pauses, and start from the first page again.
  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery(search.trim());
      setPage(0);
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, isLoading, isError } = useAdminUsers(
    { skip: page * PAGE_SIZE, limit: PAGE_SIZE, q: query, role: role || undefined },
    isAdmin
  );
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const users = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pastTheEnd = !isLoading && !isError && users.length === 0 && page > 0;

  const handleChange = async (user: AdminUser, changes: AdminUserChanges) => {
    try {
      setBusyId(user.id);
      setActionError(null);
      await updateUser.mutateAsync({ id: user.id, changes });
    } catch (err) {
      setActionError(getErrorMessage(err, "Perubahan belum tersimpan. Coba lagi."));
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async () => {
    if (!deleting) return;
    try {
      setBusyId(deleting.id);
      setActionError(null);
      await deleteUser.mutateAsync(deleting.id);
      setDeleting(null);
    } catch (err) {
      setDeleting(null);
      setActionError(getErrorMessage(err, "Akun belum bisa dihapus. Coba lagi."));
    } finally {
      setBusyId(null);
    }
  };

  if (status === "loading") {
    return <p className="py-16 text-center text-ink-soft" role="status">Memeriksa hak akses...</p>;
  }

  // Client-side fallback; the route is also guarded by middleware and the API.
  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-xl">
        <Sheet margin className="py-10 pr-6 sm:pr-10">
          <h1 className="text-3xl font-bold">Khusus administrator</h1>
          <p className="mt-3 text-ink-soft">Daftar pengguna hanya bisa dikelola oleh akun administrator.</p>
          <Link href="/lesson-plans" className={buttonVariants({ className: "mt-6" })}>
            Kembali ke modul ajar
          </Link>
        </Sheet>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl lg:text-4xl">Pengguna</h1>
        <p className="mt-2 max-w-2xl text-ink-soft" aria-live="polite">
          {isLoading ? "Memuat daftar..." : `${total} akun`}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_14rem]">
        <div className="space-y-1.5">
          <Label htmlFor="cari-pengguna">Cari nama atau email</Label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-soft" aria-hidden />
            <Input
              id="cari-pengguna"
              type="search"
              maxLength={100}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="filter-peran">Peran</Label>
          <Select
            id="filter-peran"
            value={role}
            onChange={(e) => {
              setRole(e.target.value as UserRole | "");
              setPage(0);
            }}
          >
            <option value="">Semua peran</option>
            <option value="user">Guru</option>
            <option value="admin">Administrator</option>
          </Select>
        </div>
      </div>

      {(actionError || isError) && (
        <Notice tone="error">
          <p>{actionError ?? "Daftar pengguna belum bisa dimuat. Muat ulang halaman, atau coba lagi nanti."}</p>
        </Notice>
      )}

      {pastTheEnd ? (
        <Notice tone="info">
          <p>Halaman ini sudah kosong.</p>
          <button
            type="button"
            onClick={() => setPage(pageCount - 1)}
            className="font-semibold underline underline-offset-4 hover:no-underline"
          >
            Kembali ke halaman terakhir
          </button>
        </Notice>
      ) : (
        <Sheet className="px-5 sm:px-6 lg:px-8">
          {isLoading ? (
            <p className="py-12 text-center text-ink-soft" role="status">Memuat daftar pengguna...</p>
          ) : users.length === 0 ? (
            <p className="py-12 text-center text-ink-soft">Tidak ada akun yang cocok.</p>
          ) : (
            <UserTable
              users={users}
              currentUserId={session?.user.id ?? ""}
              busyId={busyId}
              onChange={handleChange}
              onDelete={setDeleting}
            />
          )}
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} label="Halaman daftar pengguna" />
        </Sheet>
      )}

      <ConfirmDialog
        open={deleting !== null}
        title="Hapus akun ini?"
        description={
          <>
            Akun <strong className="text-foreground">{deleting?.full_name}</strong> dihapus permanen beserta semua
            modul ajarnya. Tindakan ini tidak bisa dibatalkan. Untuk menahan akses tanpa menghapus, nonaktifkan
            akunnya.
          </>
        }
        confirmLabel={deleteUser.isPending ? "Menghapus..." : "Hapus akun"}
        destructive
        pending={deleteUser.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  );
}
