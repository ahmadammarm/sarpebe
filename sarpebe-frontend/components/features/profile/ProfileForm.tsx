"use client";

import { useState } from "react";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { useUpdateProfile } from "@/lib/hooks/useUsers";
import { getErrorMessage } from "@/lib/utils/errors";
import { profileSchema, zodFieldErrors, type ProfileInput } from "@/lib/utils/validators";
import type { Profile } from "@/types/user";

type FieldName = keyof ProfileInput;

export function ProfileForm({ profile }: { profile: Profile }) {
  const update = useUpdateProfile();
  const [fullName, setFullName] = useState(profile.full_name);
  const [schoolName, setSchoolName] = useState(profile.school_name ?? "");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const dirty = fullName.trim() !== profile.full_name || schoolName.trim() !== (profile.school_name ?? "");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved(false);

    const parsed = profileSchema.safeParse({ full_name: fullName, school_name: schoolName });
    if (!parsed.success) {
      setFieldErrors(zodFieldErrors<FieldName>(parsed.error));
      return;
    }
    setFieldErrors({});

    try {
      await update.mutateAsync(parsed.data);
      setSaved(true);
    } catch (err) {
      setError(getErrorMessage(err, "Perubahan belum tersimpan. Coba lagi."));
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      <Field
        id="email"
        label="Email"
        type="email"
        value={profile.email ?? ""}
        readOnly
        disabled
        hint="Email dipakai untuk masuk dan tidak bisa diubah di sini."
      />
      <Field
        id="fullName"
        label="Nama lengkap"
        autoComplete="name"
        maxLength={100}
        value={fullName}
        onChange={(e) => {
          setFullName(e.target.value);
          setSaved(false);
        }}
        error={fieldErrors.full_name}
      />
      <Field
        id="schoolName"
        label="Sekolah (opsional)"
        autoComplete="organization"
        maxLength={150}
        value={schoolName}
        onChange={(e) => {
          setSchoolName(e.target.value);
          setSaved(false);
        }}
        error={fieldErrors.school_name}
      />

      <div aria-live="polite">
        {saved && !dirty && (
          <Notice tone="success">
            <p>Perubahan tersimpan.</p>
          </Notice>
        )}
        {error && (
          <Notice tone="error">
            <p>{error}</p>
          </Notice>
        )}
      </div>

      <Button type="submit" disabled={!dirty || update.isPending}>
        <Save aria-hidden />
        {update.isPending ? "Menyimpan..." : "Simpan perubahan"}
      </Button>
    </form>
  );
}
