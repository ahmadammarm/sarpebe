"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "./ThemeToggle";
import { Wordmark } from "./Wordmark";

// Tailwind's `md` breakpoint. From here up the inline navigation replaces the hamburger.
const DESKTOP_QUERY = "(min-width: 48rem)";

interface HeaderShellProps {
  logoHref: string;
  logoLabel: string;
  /** Inline links, shown from `md` up. */
  nav?: React.ReactNode;
  /** Controls on the right, shown from `md` up. The theme toggle is always included. */
  actions?: React.ReactNode;
  /** Content of the phone panel. Call `close` when a link or button is used. */
  panel: (close: () => void) => React.ReactNode;
  /** Max width of the content column, e.g. "max-w-6xl". */
  widthClassName?: string;
}

/**
 * The top bar shared by the landing page and the workspace.
 * Phones show only the name, the theme toggle and a hamburger; everything else lives in a panel
 * that slides down under the bar.
 */
export function HeaderShell({
  logoHref,
  logoLabel,
  nav,
  actions,
  panel,
  widthClassName = "max-w-6xl",
}: HeaderShellProps) {
  const [open, setOpen] = React.useState(false);
  const menuButtonRef = React.useRef<HTMLButtonElement>(null);
  const panelId = React.useId();
  const close = React.useCallback(() => setOpen(false), []);

  // The panel only exists on small screens; close it if the window grows past that.
  React.useEffect(() => {
    const query = window.matchMedia(DESKTOP_QUERY);
    const closeOnDesktop = (event: MediaQueryListEvent) => {
      if (event.matches) setOpen(false);
    };
    query.addEventListener("change", closeOnDesktop);
    return () => query.removeEventListener("change", closeOnDesktop);
  }, []);

  // While the menu is open the page behind it must not scroll. Both <html> and <body> are locked
  // (iOS Safari honors only one of them depending on version), and the scrollbar's width is kept
  // as padding so a desktop-width window does not jump sideways.
  React.useEffect(() => {
    if (!open) return;

    const root = document.documentElement;
    const body = document.body;
    const scrollbarWidth = window.innerWidth - root.clientWidth;
    const previous = {
      rootOverflow: root.style.overflow,
      rootPaddingRight: root.style.paddingRight,
      bodyOverflow: body.style.overflow,
    };

    root.style.overflow = "hidden";
    body.style.overflow = "hidden";
    if (scrollbarWidth > 0) root.style.paddingRight = `${scrollbarWidth}px`;

    return () => {
      root.style.overflow = previous.rootOverflow;
      root.style.paddingRight = previous.rootPaddingRight;
      body.style.overflow = previous.bodyOverflow;
    };
  }, [open]);

  return (
    <header
      className="sticky top-0 z-40 border-b border-rule bg-paper"
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          setOpen(false);
          menuButtonRef.current?.focus();
        }
      }}
    >
      <div
        className={cn(
          "mx-auto flex h-16 w-full items-center justify-between gap-3 px-5 sm:px-6 lg:px-8",
          // From md up: name | links | controls. The outer columns are equal (1fr), so the links
          // sit in the true center of the bar regardless of how wide each side is.
          "md:grid md:grid-cols-[1fr_auto_1fr] md:gap-6",
          widthClassName
        )}
      >
        <Link
          href={logoHref}
          aria-label={logoLabel}
          className="shrink-0 justify-self-start rounded-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/40"
        >
          <Wordmark />
        </Link>

        {/* From md up: links in the middle column... */}
        {nav && (
          <nav aria-label="Menu utama" className="hidden items-center justify-center gap-7 md:col-start-2 md:flex">
            {nav}
          </nav>
        )}

        {/* ...and controls in the right column. */}
        <div className="hidden min-w-0 items-center justify-end gap-2 md:col-start-3 md:flex">
          {actions}
          <ThemeToggle />
        </div>

        {/* Phones: only the theme toggle and the hamburger. */}
        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          <Button
            ref={menuButtonRef}
            type="button"
            variant="outline"
            size="icon"
            aria-expanded={open}
            aria-controls={panelId}
            aria-label={open ? "Tutup menu" : "Buka menu"}
            onClick={() => setOpen((value) => !value)}
          >
            <span className="relative size-5" aria-hidden>
              <Menu
                className={cn(
                  "absolute inset-0 size-5 transition-all duration-200",
                  open ? "rotate-90 scale-50 opacity-0" : "rotate-0 scale-100 opacity-100"
                )}
              />
              <X
                className={cn(
                  "absolute inset-0 size-5 transition-all duration-200",
                  open ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-50 opacity-0"
                )}
              />
            </span>
          </Button>
        </div>
      </div>

      {/*
        Dims everything below the bar while the menu is open; tapping it closes the menu.
        Fixed black, not a theme color: --ink is light in dark mode and would brighten the page.
      */}
      <div
        aria-hidden
        onClick={close}
        className={cn(
          "fixed inset-x-0 bottom-0 top-16 z-30 touch-none overscroll-contain bg-black/50 transition-opacity duration-300 md:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0"
        )}
      />

      <div
        id={panelId}
        data-open={open}
        className="absolute inset-x-0 top-full z-40 grid grid-rows-[0fr] bg-paper transition-[grid-template-rows] duration-300 ease-out data-[open=true]:grid-rows-[1fr] data-[open=true]:border-b data-[open=true]:border-rule data-[open=true]:shadow-lg md:hidden"
      >
        <div className="overflow-hidden" inert={!open}>
          <div
            className={cn(
              "mx-auto flex max-h-[calc(100dvh-4rem)] w-full flex-col overflow-y-auto overscroll-contain px-5 pb-6 pt-1 sm:px-6",
              widthClassName
            )}
          >
            {panel(close)}
          </div>
        </div>
      </div>
    </header>
  );
}
