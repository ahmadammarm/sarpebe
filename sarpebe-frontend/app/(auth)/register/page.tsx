import type { Metadata } from "next";
import { RegisterForm } from "@/components/features/auth/RegisterForm";

export const metadata: Metadata = { title: "Buat akun" };

export default function RegisterPage() {
  return <RegisterForm />;
}
