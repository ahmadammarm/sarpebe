"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { Sparkles, FileText, BookOpen, LogOut, User, ShieldCheck } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { data: session } = useSession();
  const role = (session?.user as any)?.role || "user";
  const isAdmin = role === "admin";

  const isCurrent = (path: string) => {
    if (path === "/lesson-plans" && (pathname === "/lesson-plans" || pathname.startsWith("/lesson-plans/"))) {
      return true;
    }
    return pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F8FAF9] text-foreground font-sans">
      {/* Sticky Dashboard Topbar */}
      <header className="sticky top-0 z-40 w-full border-b bg-white/90 backdrop-blur-md">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/lesson-plans" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-500/20">
                <Sparkles className="h-4 w-4" />
              </div>
              <span className="font-extrabold text-lg tracking-tight text-emerald-950">SARPEBE</span>
            </Link>

            <nav className="hidden md:flex items-center gap-1">
              <Link href="/lesson-plans">
                <span
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isCurrent("/lesson-plans")
                      ? "bg-emerald-50 text-emerald-800 font-semibold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <FileText className="h-4 w-4" />
                  Modul Ajar
                </span>
              </Link>
              {isAdmin && (
                <Link href="/curriculum">
                  <span
                    className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      isCurrent("/curriculum")
                        ? "bg-emerald-50 text-emerald-800 font-semibold"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    <BookOpen className="h-4 w-4" />
                    Dokumen Kurikulum
                  </span>
                </Link>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-right">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center ${isAdmin ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-700"}`}>
                {isAdmin ? <ShieldCheck className="h-4 w-4" /> : <User className="h-4 w-4" />}
              </div>
              <div className="text-xs">
                <div className="font-semibold text-slate-800 line-clamp-1">
                  {session?.user?.name || session?.user?.email || "Pendidik"}
                </div>
                <div className={isAdmin ? "text-amber-700 font-semibold" : "text-emerald-600"}>
                  {isAdmin ? "Administrator" : "Guru / Pengajar"}
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="text-slate-600 hover:text-red-600 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4 mr-1" />
              <span className="hidden sm:inline">Keluar</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 pb-16">{children}</main>
    </div>
  );
}
