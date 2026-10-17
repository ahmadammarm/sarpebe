import * as React from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { cn } from "@/lib/utils";

type Tone = "error" | "success" | "info";

const TONES: Record<Tone, { classes: string; icon: typeof Info; role: "alert" | "status" }> = {
  error: { classes: "border-margin/40 bg-margin-wash text-margin-text", icon: AlertCircle, role: "alert" },
  success: { classes: "border-tick/40 bg-tick-wash text-tick", icon: CheckCircle2, role: "status" },
  info: { classes: "border-ballpoint/30 bg-wash text-foreground", icon: Info, role: "status" },
};

/** Inline message. Errors say what went wrong; the caller adds how to fix it. */
export function Notice({
  tone = "info",
  className,
  children,
}: {
  tone?: Tone;
  className?: string;
  children: React.ReactNode;
}) {
  const { classes, icon: Icon, role } = TONES[tone];

  return (
    <div role={role} className={cn("flex gap-2.5 rounded-md border px-3 py-2.5 text-sm font-medium", classes, className)}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 space-y-1.5">{children}</div>
    </div>
  );
}
