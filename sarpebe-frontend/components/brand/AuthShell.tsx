import Link from "next/link";
import { Sheet } from "./Sheet";
import { ThemeToggle } from "./ThemeToggle";
import { Wordmark } from "./Wordmark";

interface AuthShellProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  /** Small handwritten line under the sheet. */
  note?: string;
}

/** Shared frame for sign-in, sign-up and password screens: one sheet on ruled paper. */
export function AuthShell({ title, description, children, note }: AuthShellProps) {
  return (
    <div className="ruled-page flex min-h-screen flex-col">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 pt-6 sm:px-8">
        <Link href="/" aria-label="SARPEBE, ke halaman depan" className="rounded-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
          <Wordmark />
        </Link>
        <ThemeToggle />
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4 py-10">
        <Sheet margin className="w-full max-w-lg py-8 pr-6 sm:pr-10">
          <h1 className="text-3xl font-bold leading-tight">{title}</h1>
          {description && <p className="mt-2 text-ink-soft">{description}</p>}
          <div className="mt-7">{children}</div>
        </Sheet>
        {note && <p className="mt-5 font-hand text-xl text-ink-soft">{note}</p>}
      </main>
    </div>
  );
}
