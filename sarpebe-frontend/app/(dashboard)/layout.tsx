"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/brand/ThemeToggle";
import { Wordmark } from "@/components/brand/Wordmark";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/lesson-plans", label: "Modul ajar" },
  { href: "/curriculum", label: "Dokumen kurikulum", adminOnly: true },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { data: session } = useSession();
  const isAdmin = session?.user.role === "admin";
  const displayName = session?.user.name || session?.user.email || "Pengguna";

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#konten"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-sheet focus:px-3 focus:py-2 focus:text-sm focus:font-semibold focus:shadow-lg"
      >
        Lewati ke konten
      </a>

      <header className="sticky top-0 z-40 border-b border-rule bg-paper">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-1 px-5 py-2 sm:px-8">
          <div className="flex items-center gap-8">
            <Link
              href="/lesson-plans"
              aria-label="SARPEBE, ke daftar modul ajar"
              className="rounded-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              <Wordmark />
            </Link>

            <nav aria-label="Utama" className="order-last flex w-full gap-5 sm:order-none sm:w-auto">
              {NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin).map((item) => {
                const current = pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={current ? "page" : undefined}
                    className={cn(
                      "rounded-sm py-2 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/40",
                      current ? "font-semibold text-foreground" : "text-ink-soft hover:text-foreground"
                    )}
                  >
                    <span className={cn(current && "mark")}>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-1 sm:gap-3">
            <div className="hidden text-right text-sm leading-tight sm:block">
              <div className="max-w-48 truncate font-semibold">{displayName}</div>
              <div className="text-xs text-ink-soft">{isAdmin ? "Administrator" : "Guru"}</div>
            </div>
            <ThemeToggle />
            <Button variant="ghost" size="sm" onClick={() => signOut({ callbackUrl: "/login" })}>
              <LogOut aria-hidden />
              Keluar
            </Button>
          </div>
        </div>
      </header>

      <main id="konten" className="mx-auto w-full max-w-5xl flex-1 px-5 py-8 sm:px-8 sm:py-12">
        {children}
      </main>
    </div>
  );
}
