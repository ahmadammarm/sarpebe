"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { LogOut } from "lucide-react";
import { HeaderShell } from "@/components/brand/HeaderShell";
import { Button } from "@/components/ui/button";
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
  const roleLabel = isAdmin ? "Administrator" : "Guru";
  const items = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);

  const isCurrent = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#konten"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-sheet focus:px-3 focus:py-2 focus:text-sm focus:font-semibold focus:shadow-lg"
      >
        Lewati ke konten
      </a>

      <HeaderShell
        logoHref="/lesson-plans"
        logoLabel="SARPEBE, ke daftar modul ajar"
        widthClassName="max-w-5xl"
        nav={items.map((item) => {
          const current = isCurrent(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={current ? "page" : undefined}
              className={cn(
                "rounded-sm py-2.5 text-sm outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/40",
                current ? "font-semibold text-foreground" : "text-ink-soft hover:text-foreground"
              )}
            >
              <span className={cn(current && "mark")}>{item.label}</span>
            </Link>
          );
        })}
        actions={
          <>
            <div className="hidden text-right text-sm leading-tight lg:block">
              <div className="max-w-48 truncate font-semibold">{displayName}</div>
              <div className="text-xs text-ink-soft">{roleLabel}</div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => signOut({ callbackUrl: "/login" })}>
              <LogOut aria-hidden />
              Keluar
            </Button>
          </>
        }
        panel={(close) => (
          <>
            <nav aria-label="Menu utama" className="flex flex-col">
              {items.map((item) => {
                const current = isCurrent(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={close}
                    aria-current={current ? "page" : undefined}
                    className="rounded-sm border-b border-rule py-4 text-lg font-semibold outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
                  >
                    <span className={cn(current && "mark")}>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="mt-5 flex items-center justify-between gap-4">
              <div className="min-w-0 text-sm leading-tight">
                <div className="truncate font-semibold">{displayName}</div>
                <div className="mt-0.5 text-xs text-ink-soft">{roleLabel}</div>
              </div>
              <Button
                variant="outline"
                size="lg"
                onClick={() => {
                  close();
                  void signOut({ callbackUrl: "/login" });
                }}
              >
                <LogOut aria-hidden />
                Keluar
              </Button>
            </div>
          </>
        )}
      />

      <main id="konten" className="mx-auto w-full max-w-5xl flex-1 px-5 py-6 sm:px-6 sm:py-10 lg:px-8">
        {children}
      </main>
    </div>
  );
}
