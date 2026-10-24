"use client";

import { useState } from "react";
import { signOut } from "next-auth/react";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { PasswordField } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { useDeleteAccount } from "@/lib/hooks/useUsers";
import { getErrorMessage } from "@/lib/utils/errors";
import { deleteAccountSchema } from "@/lib/utils/validators";

export function DeleteAccountSection() {
  const deleteAccount = useDeleteAccount();
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);

  const close = () => {
    setOpen(false);
    setPassword("");
    setFieldError(undefined);
    setError(null);
  };

  const handleConfirm = async () => {
    setError(null);
    const parsed = deleteAccountSchema.safeParse({ password });
    if (!parsed.success) {
      setFieldError(parsed.error.issues[0]?.message);
      return;
    }
    setFieldError(undefined);

    try {
      await deleteAccount.mutateAsync(parsed.data.password);
      await signOut({ callbackUrl: "/login?pesan=akun-dihapus" });
    } catch (err) {
      setError(getErrorMessage(err, "Akun belum bisa dihapus. Coba lagi sebentar lagi."));
    }
  };

  const busy = deleteAccount.isPending || deleteAccount.isSuccess;

  return (
    <>
      <p className="max-w-xl text-ink-soft">
        Menghapus akun juga menghapus semua modul ajar Anda. Tindakan ini tidak bisa dibatalkan.
      </p>
      <Button variant="destructive" className="mt-4" onClick={() => setOpen(true)}>
        <Trash2 aria-hidden />
        Hapus akun saya
      </Button>

      <ConfirmDialog
        open={open}
        title="Hapus akun?"
        description="Akun dan seluruh modul ajar Anda dihapus permanen. Masukkan password untuk memastikan ini Anda."
        confirmLabel={busy ? "Menghapus..." : "Hapus akun"}
        destructive
        pending={busy}
        onConfirm={handleConfirm}
        onCancel={close}
      >
        <PasswordField
          id="deletePassword"
          label="Password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={fieldError}
          disabled={busy}
        />
        {error && (
          <Notice tone="error">
            <p>{error}</p>
          </Notice>
        )}
      </ConfirmDialog>
    </>
  );
}
