"use client";

import React, { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthShell } from "@/components/brand/AuthShell";
import { Button } from "@/components/ui/button";
import { Field, PasswordField } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { loginSchema, LoginFormData, zodFieldErrors } from "@/lib/utils/validators";
import { AUTH_ERRORS } from "@/lib/utils/auth-errors";
import { useResendVerification } from "@/lib/hooks/useAuth";

const LOGIN_ERROR_MESSAGES: Record<string, string> = {
  [AUTH_ERRORS.invalidCredentials]: "Email atau password salah. Periksa lagi, atau atur ulang password Anda.",
  [AUTH_ERRORS.emailNotVerified]: "Email Anda belum diverifikasi. Buka tautan di email pendaftaran.",
  [AUTH_ERRORS.tooManyAttempts]: "Terlalu banyak percobaan gagal. Tunggu beberapa menit, lalu coba lagi.",
  [AUTH_ERRORS.serverError]: "Server tidak dapat dihubungi. Coba lagi sebentar lagi.",
};

export function LoginForm() {
  const router = useRouter();
  const resendVerification = useResendVerification();
  const [formData, setFormData] = useState<LoginFormData>({ email: "", password: "" });
  const [errors, setErrors] = useState<Partial<LoginFormData>>({});
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const needsVerification = loginError === AUTH_ERRORS.emailNotVerified;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setLoginError(null);
    resendVerification.reset();

    const parsed = loginSchema.safeParse(formData);
    if (!parsed.success) {
      setErrors(zodFieldErrors(parsed.error));
      return;
    }

    setIsLoading(true);
    try {
      const res = await signIn("credentials", {
        redirect: false,
        email: parsed.data.email,
        password: parsed.data.password,
      });

      if (res?.error) {
        setLoginError(res.error in LOGIN_ERROR_MESSAGES ? res.error : AUTH_ERRORS.serverError);
      } else {
        router.push("/lesson-plans");
        router.refresh();
      }
    } catch {
      setLoginError(AUTH_ERRORS.serverError);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      title="Masuk"
      description="Lanjutkan menyusun modul ajar Anda."
      note="Belum punya akun? Daftar dulu, hanya butuh email."
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <Field
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="nama@sekolah.sch.id"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          error={errors.email}
        />
        <PasswordField
          id="password"
          label="Password"
          autoComplete="current-password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          error={errors.password}
          labelAction={
            <Link href="/forgot-password" className="text-sm font-medium text-ballpoint underline-offset-4 hover:underline">
              Lupa password?
            </Link>
          }
        />

        {loginError && (
          <Notice tone="error">
            <p>{LOGIN_ERROR_MESSAGES[loginError]}</p>
            {needsVerification && !resendVerification.isSuccess && (
              <button
                type="button"
                className="font-semibold underline underline-offset-4 hover:no-underline disabled:opacity-50"
                disabled={resendVerification.isPending}
                onClick={() => resendVerification.mutate(formData.email)}
              >
                {resendVerification.isPending ? "Mengirim..." : "Kirim ulang email verifikasi"}
              </button>
            )}
          </Notice>
        )}

        {resendVerification.isSuccess && (
          <Notice tone="success">
            <p>Jika akun Anda menunggu verifikasi, tautan baru sudah dikirim. Periksa kotak masuk Anda.</p>
          </Notice>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={isLoading}>
          {isLoading ? "Memeriksa..." : "Masuk"}
        </Button>

        <p className="text-center text-sm text-ink-soft">
          Belum punya akun?{" "}
          <Link href="/register" className="font-semibold text-ballpoint underline-offset-4 hover:underline">
            Daftar
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
