"use client";

import { useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { Plus } from "lucide-react";
import { Sheet } from "@/components/brand/Sheet";
import { buttonVariants } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { Pagination } from "@/components/ui/pagination";
import { LessonPlanList } from "@/components/features/lesson-plans/LessonPlanList";
import { useDeleteLessonPlan, useDownloadLessonPlan, useLessonPlans, isUnfinished } from "@/lib/hooks/useLessonPlans";
import { getErrorMessage } from "@/lib/utils/errors";
import type { LessonPlan } from "@/types/lesson-plan";

const PAGE_SIZE = 10;

export function LessonPlanDashboard() {
  const { status } = useSession();
  const [page, setPage] = useState(0);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, isLoading, isError } = useLessonPlans(page * PAGE_SIZE, PAGE_SIZE, status === "authenticated");
  const deletePlan = useDeleteLessonPlan();
  const download = useDownloadLessonPlan();

  const plans = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const unfinishedCount = plans.filter((plan) => isUnfinished(plan.status)).length;

  const handleDelete = async (plan: LessonPlan) => {
    if (!confirm(`Hapus modul "${plan.topic}"? Tindakan ini tidak bisa dibatalkan.`)) return;
    try {
      setActionError(null);
      await deletePlan.mutateAsync(plan.id);
      // Deleting the only item on the last page would leave an empty page.
      if (plans.length === 1 && page > 0) setPage(page - 1);
    } catch (err) {
      setActionError(getErrorMessage(err, "Modul belum bisa dihapus. Coba lagi."));
    }
  };

  const handleDownload = async (plan: LessonPlan) => {
    try {
      setActionError(null);
      await download.mutateAsync({ id: plan.id, topic: plan.topic, format: "pdf" });
    } catch (err) {
      setActionError(getErrorMessage(err, "PDF belum bisa diunduh. Coba lagi."));
    }
  };

  if (status === "loading") {
    return <p className="py-16 text-center text-ink-soft" role="status">Memuat sesi Anda...</p>;
  }

  if (status === "unauthenticated") {
    return (
      <Notice tone="info">
        <p>Sesi Anda berakhir.</p>
        <Link href="/login" className="font-semibold underline underline-offset-4 hover:no-underline">
          Masuk lagi
        </Link>
      </Notice>
    );
  }

  const summary = isLoading
    ? "Memuat daftar..."
    : total === 0
      ? "Belum ada modul."
      : `${total} modul${unfinishedCount > 0 ? `, ${unfinishedCount} sedang disusun` : ""}`;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl lg:text-4xl">Modul ajar saya</h1>
          <p className="mt-2 text-ink-soft" aria-live="polite">{summary}</p>
        </div>
        <Link href="/lesson-plans/new" className={buttonVariants({ size: "lg" })}>
          <Plus aria-hidden />
          Buat modul ajar
        </Link>
      </div>

      {(actionError || isError) && (
        <Notice tone="error">
          <p>{actionError ?? "Daftar modul belum bisa dimuat. Muat ulang halaman, atau coba lagi nanti."}</p>
        </Notice>
      )}

      {!isLoading && !isError && total === 0 ? (
        <Sheet margin className="py-12 pr-6 sm:pr-10">
          <p className="font-hand text-3xl text-ink-soft">Halaman ini masih kosong.</p>
          <h2 className="mt-2 text-2xl font-bold">Mulai dari satu topik.</h2>
          <p className="mt-3 max-w-md text-ink-soft">
            Pilih kelas, mata pelajaran, dan topik. Modul biasanya selesai dalam 20 sampai 60 detik.
          </p>
          <Link href="/lesson-plans/new" className={buttonVariants({ className: "mt-6" })}>
            <Plus aria-hidden />
            Buat modul ajar
          </Link>
        </Sheet>
      ) : (
        <Sheet className="px-5 sm:px-6 lg:px-8">
          {isLoading ? (
            <p className="py-12 text-center text-ink-soft" role="status">Memuat daftar modul...</p>
          ) : (
            <LessonPlanList plans={plans} onDelete={handleDelete} onDownload={handleDownload} />
          )}

          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </Sheet>
      )}
    </div>
  );
}
