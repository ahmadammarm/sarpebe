import type { Metadata } from "next";
import { Suspense } from "react";
import { ResetPasswordForm } from "@/components/features/auth/ResetPasswordForm";

// Links with one-time tokens: nothing for a search engine to index.
export const metadata: Metadata = { title: "Buat password baru", robots: { index: false, follow: false } };

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
