import { AlertCircle, Check, Clock, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CurriculumDocumentStatus } from "@/types/curriculum";
import type { LessonPlanStatus } from "@/types/lesson-plan";

type Tone = "done" | "busy" | "failed";

const TONE_CLASSES: Record<Tone, string> = {
  done: "border-tick/40 bg-tick-wash text-tick",
  busy: "border-ballpoint/30 bg-wash text-ballpoint",
  failed: "border-margin/40 bg-margin-wash text-margin-text",
};

const PLAN_STATUS: Record<LessonPlanStatus, { label: string; tone: Tone; icon: typeof Check }> = {
  pending: { label: "Menunggu", tone: "busy", icon: Clock },
  processing: { label: "Disusun", tone: "busy", icon: Loader2 },
  completed: { label: "Siap", tone: "done", icon: Check },
  failed: { label: "Gagal", tone: "failed", icon: AlertCircle },
};

const DOCUMENT_STATUS: Record<CurriculumDocumentStatus, { label: string; tone: Tone; icon: typeof Check }> = {
  processing: { label: "Memproses", tone: "busy", icon: Loader2 },
  completed: { label: "Terindeks", tone: "done", icon: Check },
  failed: { label: "Gagal", tone: "failed", icon: AlertCircle },
};

type StatusStampProps =
  | { kind: "plan"; status: LessonPlanStatus; className?: string }
  | { kind: "document"; status: CurriculumDocumentStatus; className?: string };

/** Status as icon + word, so it never relies on color alone. */
export function StatusStamp(props: StatusStampProps) {
  const { label, tone, icon: Icon } =
    props.kind === "plan" ? PLAN_STATUS[props.status] : DOCUMENT_STATUS[props.status];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-semibold",
        TONE_CLASSES[tone],
        props.className
      )}
    >
      <Icon className={cn("size-3.5", Icon === Loader2 && "animate-spin")} aria-hidden />
      {label}
    </span>
  );
}
