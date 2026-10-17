import type { Metadata } from "next";
import { Suspense } from "react";
import { VerifyEmailStatus } from "@/components/features/auth/VerifyEmailStatus";

export const metadata: Metadata = { title: "Verifikasi email" };

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailStatus />
    </Suspense>
  );
}
