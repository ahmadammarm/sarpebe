"use client";

import { useParams, useRouter } from "next/navigation";
import { useCreateLessonPlan, useLessonPlan } from "@/lib/hooks/useLessonPlans";
import { getErrorMessage } from "@/lib/utils/errors";
import { LessonPlanEditor } from "@/components/features/lesson-plans/LessonPlanEditor";
import { Button } from "@/components/ui/button";
import { ArrowLeft, AlertCircle, Loader2, RefreshCw } from "lucide-react";

export default function LessonPlanDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const { data: plan, isLoading, isError } = useLessonPlan(id);
  const regenerate = useCreateLessonPlan();

  const handleRegenerate = async () => {
    if (!plan) return;
    try {
      const created = await regenerate.mutateAsync({
        grade_level: plan.grade_level,
        subject: plan.subject,
        topic: plan.topic,
      });
      router.push(`/lesson-plans/${created.id}`);
    } catch {
      // surfaced below through regenerate.error
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center">Memuat Rencana Pembelajaran...</div>;
  }

  if (isError || !plan) {
    return <div className="p-8 text-center text-red-500">Rencana Pembelajaran tidak ditemukan.</div>;
  }

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <Button
        variant="ghost"
        className="mb-6"
        onClick={() => router.push("/lesson-plans")}
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Kembali ke Daftar
      </Button>

      {(plan.status === "pending" || plan.status === "processing") && (
        <div className="py-16 text-center space-y-4 bg-white border border-slate-200/80 rounded-2xl shadow-xs">
          <Loader2 className="h-10 w-10 animate-spin text-emerald-600 mx-auto" />
          <h2 className="text-lg font-bold text-emerald-950">AI Sedang Menyusun Modul Ajar...</h2>
          <p className="text-sm text-slate-500">
            Topik: <strong>{plan.topic}</strong>. Halaman ini akan diperbarui otomatis setelah selesai.
          </p>
        </div>
      )}

      {plan.status === "failed" && (
        <div className="py-12 px-6 text-center space-y-4 bg-white border border-rose-100 rounded-2xl shadow-xs">
          <div className="h-14 w-14 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
            <AlertCircle className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Gagal Menyusun Modul Ajar</h2>
          <p className="text-sm text-slate-600 max-w-md mx-auto">
            {plan.generated_content?.error ?? "Terjadi kendala saat menyusun modul ajar ini."}
          </p>
          {regenerate.isError && (
            <p className="text-sm text-rose-600">
              {getErrorMessage(regenerate.error, "Gagal memulai pembuatan ulang.")}
            </p>
          )}
          <Button
            onClick={handleRegenerate}
            disabled={regenerate.isPending}
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {regenerate.isPending ? "Memulai..." : "Buat Ulang"}
          </Button>
        </div>
      )}

      {plan.status === "completed" && <LessonPlanEditor key={plan.id} plan={plan} />}
    </div>
  );
}
