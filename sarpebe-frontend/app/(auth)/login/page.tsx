import type { Metadata } from "next";
import { LoginForm } from "@/components/features/auth/LoginForm";

export const metadata: Metadata = { title: "Masuk" };

// Only these keys are accepted, so the page never echoes text taken from the address bar.
const NOTICES: Record<string, string> = {
  "password-diganti": "Password sudah diganti. Masuk lagi dengan password baru.",
  "akun-dihapus": "Akun Anda sudah dihapus beserta seluruh modul ajarnya.",
};

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ pesan?: string }> }) {
  const { pesan } = await searchParams;
  return <LoginForm notice={pesan ? NOTICES[pesan] : undefined} />;
}
