import { Check, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { GenerationStage, LessonPlanStatus } from "@/types/lesson-plan";

const STEPS = [
  { key: "pending", label: "Menunggu giliran" },
  { key: "retrieving", label: "Mencari bagian CP yang relevan" },
  { key: "drafting", label: "Menyusun modul" },
  { key: "repairing", label: "Memeriksa waktu dan tabel" },
  { key: "completed", label: "Modul siap" },
] as const;

function stepIndex(status: LessonPlanStatus, stage: GenerationStage | null | undefined): number {
  if (status === "completed") return STEPS.length - 1;
  if (status !== "processing") return 0;
  const index = STEPS.findIndex((step) => step.key === stage);
  return index === -1 ? 1 : index;
}

/**
 * The real stages a generation job goes through. The backend reports which one it is in, so
 * what is shown here is what is actually happening.
 */
export function GenerationProgress({
  status,
  stage,
}: {
  status: LessonPlanStatus;
  stage?: GenerationStage | null;
}) {
  const current = stepIndex(status, stage);

  return (
    <ol className="space-y-3" aria-label="Tahap penyusunan modul">
      {STEPS.map((step, index) => {
        const done = index < current || status === "completed";
        const active = index === current && status !== "completed";

        return (
          <li
            key={step.key}
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
            <span className={cn(active && "font-semibold")}>{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
