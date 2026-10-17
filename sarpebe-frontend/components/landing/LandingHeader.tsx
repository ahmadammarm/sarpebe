"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { HeaderShell } from "@/components/brand/HeaderShell";
import { buttonVariants } from "@/components/ui/button";
import { LANDING_MENU } from "@/components/landing/menu";
import { cn } from "@/lib/utils";

const MENU_IDS: readonly string[] = LANDING_MENU.map((item) => item.id);

/** The id of the menu section crossing the middle of the viewport, or null elsewhere. */
function useActiveSection(): string | null {
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    const sections = document.querySelectorAll<HTMLElement>("main section[id]");
    if (!sections.length || !("IntersectionObserver" in window)) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(MENU_IDS.includes(entry.target.id) ? entry.target.id : null);
          }
        }
      },
      { rootMargin: "-35% 0px -55% 0px" }
    );
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  return activeId;
}

export function LandingHeader() {
  const activeId = useActiveSection();

  return (
    <HeaderShell
      logoHref="/"
      logoLabel="SARPEBE, ke halaman depan"
      widthClassName="max-w-6xl"
      nav={LANDING_MENU.map((item) => {
        const current = activeId === item.id;
        return (
          <a
            key={item.id}
            href={`#${item.id}`}
            aria-current={current ? "location" : undefined}
            className={cn(
              "rounded-sm py-2 text-sm outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/40",
              current ? "font-semibold text-foreground" : "text-ink-soft hover:text-foreground"
            )}
          >
            <span className={cn(current && "mark")}>{item.label}</span>
          </a>
        );
      })}
      actions={
        <>
          <Link href="/login" className={buttonVariants({ variant: "ghost" })}>
            Masuk
          </Link>
          <Link href="/register" className={buttonVariants()}>
            Buat akun
          </Link>
        </>
      }
      panel={(close) => (
        <nav aria-label="Menu utama" className="flex flex-col">
          {LANDING_MENU.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              onClick={close}
              aria-current={activeId === item.id ? "location" : undefined}
              className="rounded-sm border-b border-rule py-4 text-lg font-semibold outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              {item.label}
            </a>
          ))}
          <div className="mt-5 grid gap-3 min-[420px]:grid-cols-2">
            <Link href="/login" onClick={close} className={buttonVariants({ variant: "outline", size: "lg" })}>
              Masuk
            </Link>
            <Link href="/register" onClick={close} className={buttonVariants({ size: "lg" })}>
              Buat akun
            </Link>
          </div>
        </nav>
      )}
    />
  );
}
