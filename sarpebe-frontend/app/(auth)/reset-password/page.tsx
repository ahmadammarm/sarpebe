import type { Metadata } from "next";
import { Suspense } from "react";
import { ResetPasswordForm } from "@/components/features/auth/ResetPasswordForm";

export const metadata: Metadata = { title: "Buat password baru" };

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
