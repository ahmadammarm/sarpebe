import { cn } from "@/lib/utils";

/** A margin rule from a notebook page, followed by the name. */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-stretch gap-2.5 font-display text-xl font-bold tracking-tight text-foreground", className)}>
      <span aria-hidden className="w-0.5 rounded-full bg-margin" />
      <span className="py-0.5 leading-none">sarpebe</span>
    </span>
  );
}
