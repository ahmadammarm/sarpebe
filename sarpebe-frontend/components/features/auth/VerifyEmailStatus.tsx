"use client";

import { useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AuthShell } from "@/components/brand/AuthShell";
import { buttonVariants } from "@/components/ui/button";
import { useVerifyEmail } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";

export function VerifyEmailStatus() {
  const token = useSearchParams().get("token");
  const verify = useVerifyEmail();
  const { mutate } = verify;
  // React strict mode runs effects twice in development; a link must only be redeemed once.
  const requested = useRef(false);

  useEffect(() => {
    if (token && !requested.current) {
      requested.current = true;
      mutate(token);
    }
  }, [token, mutate]);

  if (!token || verify.isError) {
    return (
      <AuthShell
        title="Verifikasi gagal"
        description={
          token
            ? getErrorMessage(verify.error, "Tautan ini tidak valid atau sudah kedaluwarsa.")
            : "Tautan ini tidak membawa kode verifikasi."
        }
      >
        <div className="space-y-4 text-ink-soft">
          <p>Masuk dengan akun Anda, lalu pilih kirim ulang email verifikasi.</p>
          <Link href="/login" className={buttonVariants({ size: "lg", className: "w-full" })}>
            Ke halaman masuk
          </Link>
        </div>
      </AuthShell>
    );
  }

  if (verify.isSuccess) {
    return (
      <AuthShell title="Email terverifikasi" description="Akun Anda sudah aktif dan siap dipakai.">
        <Link href="/login" className={buttonVariants({ size: "lg", className: "w-full" })}>
          Masuk
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Memverifikasi email..." description="Sebentar saja.">
      <div aria-live="polite" className="sr-only">Memverifikasi email</div>
    </AuthShell>
  );
}
