import type { Metadata } from "next";
import { Suspense } from "react";
import { VerifyEmailStatus } from "@/components/features/auth/VerifyEmailStatus";

// Links with one-time tokens: nothing for a search engine to index.
export const metadata: Metadata = { title: "Verifikasi email", robots: { index: false, follow: false } };

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailStatus />
    </Suspense>
  );
}
