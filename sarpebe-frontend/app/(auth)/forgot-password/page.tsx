import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/features/auth/ForgotPasswordForm";

export const metadata: Metadata = { title: "Lupa password" };

export default function ForgotPasswordPage() {
  return <ForgotPasswordForm />;
}
