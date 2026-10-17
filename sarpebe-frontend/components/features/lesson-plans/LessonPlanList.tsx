import Link from "next/link";
import { Download, Pencil, Trash2 } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { StatusStamp } from "@/components/brand/StatusStamp";
import { buttonVariants, Button } from "@/components/ui/button";
import type { LessonPlan } from "@/types/lesson-plan";

interface LessonPlanListProps {
  plans: LessonPlan[];
  onDelete: (plan: LessonPlan) => void;
  onDownload: (plan: LessonPlan) => void;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}

/** One ruled row per lesson plan: what it is, where it stands, and what you can do with it. */
export function LessonPlanList({ plans, onDelete, onDownload }: LessonPlanListProps) {
  return (
    <ul className="divide-y divide-rule">
      {plans.map((plan) => (
        <li key={plan.id} className="grid gap-3 py-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:gap-6">
          <div className="min-w-0">
            <Link
              href={`/lesson-plans/${plan.id}`}
              className="rounded-sm font-display text-xl font-semibold leading-snug underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring/40"
            >
              {plan.topic}
            </Link>
            <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-soft">
              <span>Kelas {plan.grade_level}</span>
              <FaseTag grade={plan.grade_level} />
              <span aria-hidden>·</span>
              <span>{plan.subject}</span>
              <span aria-hidden>·</span>
              <time dateTime={plan.created_at}>{formatDate(plan.created_at)}</time>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <StatusStamp kind="plan" status={plan.status} />
            <Link
              href={`/lesson-plans/${plan.id}`}
              className={buttonVariants({ variant: "outline", size: "sm" })}
              aria-label={`Buka modul ${plan.topic}`}
            >
              <Pencil aria-hidden />
              Buka
            </Link>
            {plan.status === "completed" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload(plan)}
                aria-label={`Unduh PDF modul ${plan.topic}`}
              >
                <Download aria-hidden />
                PDF
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => onDelete(plan)}
              aria-label={`Hapus modul ${plan.topic}`}
              className="text-ink-soft hover:bg-margin-wash hover:text-margin-text"
            >
              <Trash2 aria-hidden />
            </Button>
          </div>
        </li>
      ))}
    </ul>
  );
}
