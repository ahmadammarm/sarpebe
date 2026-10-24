"use client";

import { useState } from "react";
import { signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { PasswordField } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { useChangePassword } from "@/lib/hooks/useUsers";
import { getErrorMessage } from "@/lib/utils/errors";
import { changePasswordSchema, zodFieldErrors, type ChangePasswordInput } from "@/lib/utils/validators";

const EMPTY: ChangePasswordInput = { current_password: "", new_password: "", confirm_password: "" };

export function ChangePasswordForm() {
  const changePassword = useChangePassword();
  const [values, setValues] = useState<ChangePasswordInput>(EMPTY);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof ChangePasswordInput, string>>>({});
  const [error, setError] = useState<string | null>(null);

  const set = (field: keyof ChangePasswordInput) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setValues((previous) => ({ ...previous, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const parsed = changePasswordSchema.safeParse(values);
    if (!parsed.success) {
      setFieldErrors(zodFieldErrors<keyof ChangePasswordInput>(parsed.error));
      return;
    }
    setFieldErrors({});

    try {
      await changePassword.mutateAsync(parsed.data);
      // The backend ended every session, this one included, so the old tokens are useless now.
      await signOut({ callbackUrl: "/login?pesan=password-diganti" });
    } catch (err) {
      setError(getErrorMessage(err, "Password belum bisa diganti. Coba lagi sebentar lagi."));
    }
  };

  const busy = changePassword.isPending || changePassword.isSuccess;

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <PasswordField
        id="currentPassword"
        label="Password saat ini"
        autoComplete="current-password"
        value={values.current_password}
        onChange={set("current_password")}
        error={fieldErrors.current_password}
        disabled={busy}
      />
      <PasswordField
        id="newPassword"
        label="Password baru"
        autoComplete="new-password"
        value={values.new_password}
        onChange={set("new_password")}
        error={fieldErrors.new_password}
        hint="Minimal 8 karakter."
        disabled={busy}
      />
      <PasswordField
        id="confirmPassword"
        label="Ulangi password baru"
        autoComplete="new-password"
        value={values.confirm_password}
        onChange={set("confirm_password")}
        error={fieldErrors.confirm_password}
        disabled={busy}
      />

      <Notice tone="info">
        <p>Setelah password diganti, Anda keluar dari semua perangkat dan perlu masuk lagi.</p>
      </Notice>

      {error && (
        <Notice tone="error">
          <p>{error}</p>
        </Notice>
      )}

      <Button type="submit" disabled={busy}>
        {busy ? "Menyimpan..." : "Ganti password"}
      </Button>
    </form>
  );
}
