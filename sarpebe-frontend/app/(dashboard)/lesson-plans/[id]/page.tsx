"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { Sheet } from "@/components/brand/Sheet";
import { Button, buttonVariants } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { GenerationProgress } from "@/components/features/lesson-plans/GenerationProgress";
import { LessonPlanEditor } from "@/components/features/lesson-plans/LessonPlanEditor";
import { LessonPlanEditorV2 } from "@/components/features/lesson-plans/LessonPlanEditorV2";
import { useCreateLessonPlan, useLessonPlan } from "@/lib/hooks/useLessonPlans";
import { getErrorMessage } from "@/lib/utils/errors";
import { describeFailure } from "@/lib/utils/lesson-plan";

export default function LessonPlanDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const { data: plan, isLoading, isError } = useLessonPlan(id);
  const regenerate = useCreateLessonPlan();

  const handleRegenerate = async () => {
    if (!plan) return;
    const options = plan.request_options;
    try {
      const created = await regenerate.mutateAsync({
        grade_level: plan.grade_level,
        subject: plan.subject,
        topic: plan.topic,
        meeting_count: options?.meeting_count ?? 1,
        minutes_per_meeting: options?.minutes_per_meeting ?? 80,
        teaching_model: options?.teaching_model ?? "otomatis",
        class_notes: options?.class_notes ?? "",
      });
      router.push(`/lesson-plans/${created.id}`);
    } catch {
      // surfaced below through regenerate.error
    }
  };

  if (isLoading) {
    return <p className="py-16 text-center text-ink-soft" role="status">Memuat modul ajar...</p>;
  }

  if (isError || !plan) {
    return (
      <div className="mx-auto max-w-xl space-y-4">
        <Notice tone="error">
          <p>Modul ajar tidak ditemukan. Mungkin sudah dihapus.</p>
        </Notice>
        <Link href="/lesson-plans" className={buttonVariants({ variant: "outline" })}>
          Kembali ke daftar
        </Link>
      </div>
    );
  }

  if (plan.status === "completed") {
    return plan.schema_version === 2 ? (
      <LessonPlanEditorV2 key={plan.id} plan={plan} />
    ) : (
      <LessonPlanEditor key={plan.id} plan={plan} />
    );
  }

  const failure = describeFailure(plan.generated_content?.error);

  return (
    <div className="mx-auto max-w-2xl">
      <Link
        href="/lesson-plans"
        className="inline-flex items-center gap-1.5 rounded-sm text-sm font-medium text-ink-soft outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/40"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Modul ajar saya
      </Link>

      <Sheet margin className="mt-4 py-8 pr-6 sm:pr-10">
        {plan.status === "failed" ? (
          <div role="alert">
            <h1 className="text-3xl font-bold">Modul belum berhasil disusun</h1>
            <p className="mt-2 text-ink-soft">
              {plan.topic} · Kelas {plan.grade_level} · {plan.subject}
            </p>
            <p className="mt-5 text-lg">{failure.message}</p>
            {failure.hint && <p className="mt-2 text-ink-soft">{failure.hint}</p>}
            {regenerate.isError && (
              <Notice tone="error" className="mt-5">
                <p>{getErrorMessage(regenerate.error, "Pembuatan ulang belum bisa dimulai. Coba lagi.")}</p>
              </Notice>
            )}
            <Button onClick={handleRegenerate} disabled={regenerate.isPending} className="mt-6">
              <RefreshCw aria-hidden />
              {regenerate.isPending ? "Memulai..." : "Buat ulang"}
            </Button>
          </div>
        ) : (
          <div aria-live="polite">
            <h1 className="text-3xl font-bold">Sedang menyusun modul</h1>
            <p className="mt-2 text-ink-soft">
              {plan.topic} · Kelas {plan.grade_level} · {plan.subject}
            </p>
            <div className="mt-7">
              <GenerationProgress status={plan.status} />
            </div>
            <p className="mt-6 font-hand text-xl text-ink-soft">
              Halaman ini diperbarui sendiri saat modul selesai.
            </p>
          </div>
        )}
      </Sheet>
    </div>
  );
}
