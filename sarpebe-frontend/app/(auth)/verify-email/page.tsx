import { Suspense } from "react";
import { VerifyEmailStatus } from "@/components/features/auth/VerifyEmailStatus";

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Suspense fallback={null}>
        <VerifyEmailStatus />
      </Suspense>
    </div>
  );
}
