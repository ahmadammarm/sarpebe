"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AuthShell } from "@/components/brand/AuthShell";
import { Button, buttonVariants } from "@/components/ui/button";
import { PasswordField } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { resetPasswordSchema, ResetPasswordInput, zodFieldErrors } from "@/lib/utils/validators";
import { useResetPassword } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";

export function ResetPasswordForm() {
  const token = useSearchParams().get("token") ?? "";
  const resetPassword = useResetPassword(token);
  const [formData, setFormData] = useState<ResetPasswordInput>({ password: "", confirmPassword: "" });
  const [errors, setErrors] = useState<Partial<ResetPasswordInput>>({});
  const [globalError, setGlobalError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setGlobalError("");

    const parsed = resetPasswordSchema.safeParse(formData);
    if (!parsed.success) {
      setErrors(zodFieldErrors(parsed.error));
      return;
    }

    try {
      await resetPassword.mutateAsync(parsed.data);
    } catch (error) {
      setGlobalError(getErrorMessage(error, "Password belum bisa diubah. Coba lagi sebentar lagi."));
    }
  };

  if (!token) {
    return (
      <AuthShell title="Tautan tidak lengkap">
        <div className="space-y-4 text-ink-soft">
          <p>Tautan ini tidak membawa kode pengaman. Minta tautan baru.</p>
          <Link href="/forgot-password" className="inline-block font-semibold text-ballpoint underline-offset-4 hover:underline">
            Minta tautan baru
          </Link>
        </div>
      </AuthShell>
    );
  }

  if (resetPassword.isSuccess) {
    return (
      <AuthShell title="Password sudah diganti" description="Anda keluar dari semua perangkat. Masuk lagi dengan password baru.">
        <Link href="/login" className={buttonVariants({ size: "lg", className: "w-full" })}>
          Masuk
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Buat password baru" description="Pilih password yang belum pernah Anda pakai di tempat lain.">
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <PasswordField
          id="password"
          label="Password baru"
          autoComplete="new-password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          error={errors.password}
          hint="Minimal 8 karakter."
        />
        <PasswordField
          id="confirmPassword"
          label="Ulangi password baru"
          autoComplete="new-password"
          value={formData.confirmPassword}
          onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
          error={errors.confirmPassword}
        />

        {globalError && (
          <Notice tone="error">
            <p>{globalError}</p>
            <Link href="/forgot-password" className="font-semibold underline underline-offset-4 hover:no-underline">
              Minta tautan baru
            </Link>
          </Notice>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={resetPassword.isPending}>
          {resetPassword.isPending ? "Menyimpan..." : "Simpan password baru"}
        </Button>
      </form>
    </AuthShell>
  );
}
