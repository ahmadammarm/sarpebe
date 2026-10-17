"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AuthShell } from "@/components/brand/AuthShell";
import { Button } from "@/components/ui/button";
import { Field, PasswordField } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { registerSchema, RegisterFormData, zodFieldErrors } from "@/lib/utils/validators";
import { useRegister } from "@/lib/hooks/useAuth";
import { getErrorMessage } from "@/lib/utils/errors";

export function RegisterForm() {
  const register = useRegister();
  const [formData, setFormData] = useState<RegisterFormData>({ fullName: "", email: "", password: "" });
  const [errors, setErrors] = useState<Partial<RegisterFormData>>({});
  const [globalError, setGlobalError] = useState("");
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setGlobalError("");

    const parsed = registerSchema.safeParse(formData);
    if (!parsed.success) {
      setErrors(zodFieldErrors(parsed.error));
      return;
    }

    try {
      await register.mutateAsync(parsed.data);
      setRegisteredEmail(parsed.data.email);
    } catch (error) {
      setGlobalError(getErrorMessage(error, "Akun belum bisa dibuat. Coba lagi sebentar lagi."));
    }
  };

  if (registeredEmail) {
    return (
      <AuthShell title="Cek email Anda" description="Satu langkah lagi sebelum akun aktif.">
        <div className="space-y-4 text-ink-soft">
          <p>
            Jika <strong className="text-foreground">{registeredEmail}</strong> bisa didaftarkan, kami sudah
            mengirim tautan verifikasi ke alamat itu. Buka tautannya, lalu masuk.
          </p>
          <p>
            Sudah pernah mendaftar dengan email ini?{" "}
            <Link href="/forgot-password" className="font-semibold text-ballpoint underline-offset-4 hover:underline">
              Atur ulang password
            </Link>
            .
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
      title="Buat akun"
      description="Akun dipakai untuk menyusun dan menyimpan modul ajar Anda."
      note="Email hanya dipakai untuk verifikasi dan atur ulang password."
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <Field
          id="fullName"
          label="Nama lengkap"
          autoComplete="name"
          placeholder="Nama yang ingin ditampilkan"
          value={formData.fullName}
          onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
          error={errors.fullName}
        />
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
          autoComplete="new-password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          error={errors.password}
          hint="Minimal 8 karakter."
        />

        {globalError && (
          <Notice tone="error">
            <p>{globalError}</p>
          </Notice>
        )}

        <Button type="submit" size="lg" className="w-full" disabled={register.isPending}>
          {register.isPending ? "Membuat akun..." : "Buat akun"}
        </Button>

        <p className="text-center text-sm text-ink-soft">
          Sudah punya akun?{" "}
          <Link href="/login" className="font-semibold text-ballpoint underline-offset-4 hover:underline">
            Masuk
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
