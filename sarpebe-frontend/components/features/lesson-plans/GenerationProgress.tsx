import { Check, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LessonPlanStatus } from "@/types/lesson-plan";

const STAGES = [
  { key: "pending", label: "Menunggu giliran" },
  { key: "processing", label: "Membaca CP dan menyusun modul" },
  { key: "completed", label: "Modul siap" },
] as const;

type StageKey = (typeof STAGES)[number]["key"];

function stageIndex(status: LessonPlanStatus): number {
  const index = STAGES.findIndex((stage) => stage.key === (status as StageKey));
  return index === -1 ? 0 : index;
}

/**
 * The real stages a generation job goes through. Each stage maps to a status the backend
 * reports, so what is shown here is what is actually happening.
 */
export function GenerationProgress({ status }: { status: LessonPlanStatus }) {
  const current = stageIndex(status);

  return (
    <ol className="space-y-3" aria-label="Tahap penyusunan modul">
      {STAGES.map((stage, index) => {
        const done = index < current || status === "completed";
        const active = index === current && status !== "completed";

        return (
          <li
            key={stage.key}
            aria-current={active ? "step" : undefined}
            className={cn("flex items-center gap-3 transition-colors duration-300", !done && !active && "text-ink-soft")}
          >
            <span
              className={cn(
                "flex size-6 shrink-0 items-center justify-center rounded-full border transition-colors duration-300",
                done && "border-tick/40 bg-tick-wash text-tick",
                active && "border-ballpoint/40 bg-wash text-ballpoint",
                !done && !active && "border-rule-strong"
              )}
            >
              {done ? (
                <Check className="pop size-3.5" aria-hidden />
              ) : active ? (
                <Loader2 className="size-3.5 animate-spin" aria-hidden />
              ) : (
                <Circle className="size-2 fill-current" aria-hidden />
              )}
            </span>
            <span className={cn(active && "font-semibold")}>{stage.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
