"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AuthShell } from "@/components/brand/AuthShell";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { forgotPasswordSchema, zodFieldErrors } from "@/lib/utils/validators";
import { useForgotPassword } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";

export function ForgotPasswordForm() {
  const forgotPassword = useForgotPassword();
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | undefined>();
  const [globalError, setGlobalError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError(undefined);
    setGlobalError("");

    const parsed = forgotPasswordSchema.safeParse({ email });
    if (!parsed.success) {
      setEmailError(zodFieldErrors<"email">(parsed.error).email);
      return;
    }

    try {
      await forgotPassword.mutateAsync(parsed.data);
    } catch (error) {
      setGlobalError(getErrorMessage(error, "Tautan belum bisa dikirim. Coba lagi sebentar lagi."));
    }
  };

  if (forgotPassword.isSuccess) {
    return (
      <AuthShell title="Cek email Anda">
        <div className="space-y-4 text-ink-soft">
          <p>
            Jika ada akun untuk <strong className="text-foreground">{email}</strong>, kami sudah mengirim tautan
            untuk membuat password baru. Tautan berlaku satu jam.
          </p>
          <Link href="/login" className="inline-block font-semibold text-ballpoint underline-offset-4 hover:underline">
            Kembali ke halaman masuk
          </Link>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Lupa password"
      description="Masukkan email akun Anda. Kami kirim tautan untuk membuat password baru."
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <Field
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="nama@sekolah.sch.id"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={emailError}
        />

        {globalError && (
          <Notice tone="error">
            <p>{globalError}</p>
          </Notice>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={forgotPassword.isPending}>
          {forgotPassword.isPending ? "Mengirim..." : "Kirim tautan"}
        </Button>

        <p className="text-center text-sm text-ink-soft">
          <Link href="/login" className="font-semibold text-ballpoint underline-offset-4 hover:underline">
            Kembali ke halaman masuk
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
