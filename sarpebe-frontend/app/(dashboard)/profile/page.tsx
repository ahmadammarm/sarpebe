"use client";

import { useSession } from "next-auth/react";
import { Sheet } from "@/components/brand/Sheet";
import { ChangePasswordForm } from "@/components/features/profile/ChangePasswordForm";
import { DeleteAccountSection } from "@/components/features/profile/DeleteAccountSection";
import { ProfileForm } from "@/components/features/profile/ProfileForm";
import { QuotaSummary } from "@/components/features/profile/QuotaSummary";
import { Notice } from "@/components/ui/notice";
import { useProfile, useQuota } from "@/lib/hooks/useUsers";

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <Sheet margin className="py-8 pr-6 sm:pr-10">
      <section aria-labelledby={id}>
        <h2 id={id} className="text-2xl font-bold">
          {title}
        </h2>
        <div className="mt-5">{children}</div>
      </section>
    </Sheet>
  );
}

export default function ProfilePage() {
  const { status } = useSession();
  const enabled = status === "authenticated";
  const { data: profile, isLoading, isError } = useProfile(enabled);
  const { data: quota } = useQuota(enabled);

  if (status === "loading" || isLoading) {
    return <p className="py-16 text-center text-ink-soft" role="status">Memuat profil...</p>;
  }

  if (isError || !profile) {
    return (
      <div className="mx-auto max-w-xl">
        <Notice tone="error">
          <p>Profil belum bisa dimuat. Muat ulang halaman, atau coba lagi nanti.</p>
        </Notice>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl lg:text-4xl">Profil</h1>
        <p className="mt-2 text-ink-soft">Data akun Anda, password, dan batas penyusunan modul.</p>
      </div>

      <Section id="data-diri" title="Data diri">
        <ProfileForm key={profile.id} profile={profile} />
      </Section>

      {quota && (
        <Section id="kuota" title="Modul yang bisa disusun">
          <QuotaSummary quota={quota} />
        </Section>
      )}

      <Section id="ganti-password" title="Ganti password">
        <ChangePasswordForm />
      </Section>

      <Section id="hapus-akun" title="Hapus akun">
        <DeleteAccountSection />
      </Section>
    </div>
  );
}
