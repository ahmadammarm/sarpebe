"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Sheet } from "@/components/brand/Sheet";
import { Button, buttonVariants } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { GenerationProgress } from "@/components/features/lesson-plans/GenerationProgress";
import { useCreateLessonPlan } from "@/lib/hooks/useLessonPlans";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import { getErrorMessage } from "@/lib/utils/errors";
import { describeFailure } from "@/lib/utils/lesson-plan";
import { faseForGrade } from "@/lib/utils/fase";
import { lessonPlanCreateSchema, zodFieldErrors } from "@/lib/utils/validators";

type FieldName = "grade_level" | "subject" | "topic";

export default function NewLessonPlanPage() {
  const router = useRouter();
  const createPlan = useCreateLessonPlan();

  const [gradeLevel, setGradeLevel] = useState("");
  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");

  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [createdPlanId, setCreatedPlanId] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { status: jobStatus, isDone, error: jobError } = useJobStatus(activeJobId);
  const fase = faseForGrade(gradeLevel);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const parsed = lessonPlanCreateSchema.safeParse({ grade_level: gradeLevel, subject, topic });
    if (!parsed.success) {
      setFieldErrors(zodFieldErrors<FieldName>(parsed.error));
      return;
    }
    setFieldErrors({});

    try {
      const response = await createPlan.mutateAsync(parsed.data);
      setCreatedPlanId(response.id);
      setActiveJobId(response.job_id);
    } catch (err) {
      setErrorMsg(getErrorMessage(err, "Modul belum bisa dibuat. Coba lagi sebentar lagi."));
    }
  };

  useEffect(() => {
    if (isDone && jobStatus === "completed" && createdPlanId) {
      const timer = setTimeout(() => router.push(`/lesson-plans/${createdPlanId}`), 700);
      return () => clearTimeout(timer);
    }
  }, [isDone, jobStatus, createdPlanId, router]);

  const failed = jobStatus === "failed";
  const failure = describeFailure(jobError);

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
        {!activeJobId ? (
          <>
            <h1 className="text-3xl font-bold">Modul ajar baru</h1>
            <p className="mt-2 text-ink-soft">
              Modul disusun dari dokumen CP yang tersedia untuk kelas dan mata pelajaran yang Anda pilih.
            </p>

            <form onSubmit={handleGenerate} className="mt-7 space-y-5" noValidate>
              <Field
                id="gradeLevel"
                label="Kelas"
                placeholder="9"
                maxLength={20}
                value={gradeLevel}
                onChange={(e) => setGradeLevel(e.target.value)}
                error={fieldErrors.grade_level}
                hint={
                  fase ? (
                    <span className="inline-flex items-center gap-2">
                      <FaseTag grade={gradeLevel} /> mencakup {fase.grades}
                    </span>
                  ) : (
                    "Tulis angka kelasnya saja, misalnya 9."
                  )
                }
              />
              <Field
                id="subject"
                label="Mata pelajaran"
                placeholder="IPS"
                maxLength={100}
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                error={fieldErrors.subject}
                hint="Tulis sama seperti label pada dokumen CP yang diunggah."
              />
              <Field
                id="topic"
                label="Topik"
                placeholder="Pelaku dan kegiatan ekonomi"
                maxLength={300}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                error={fieldErrors.topic}
                hint="Satu topik untuk satu modul."
              />

              {errorMsg && (
                <Notice tone="error">
                  <p>{errorMsg}</p>
                </Notice>
              )}

              <Button type="submit" size="lg" className="w-full sm:w-auto" disabled={createPlan.isPending}>
                {createPlan.isPending ? "Mengirim..." : "Susun modul ajar"}
              </Button>
            </form>
          </>
        ) : failed ? (
          <div role="alert">
            <h1 className="text-3xl font-bold">Modul belum berhasil disusun</h1>
            <p className="mt-3 text-lg">{failure.message}</p>
            {failure.hint && <p className="mt-2 text-ink-soft">{failure.hint}</p>}
            <div className="mt-6 flex flex-wrap gap-3">
              <Button
                onClick={() => {
                  setActiveJobId(null);
                  setCreatedPlanId(null);
                }}
              >
                Ubah isian dan coba lagi
              </Button>
              <Link href="/lesson-plans" className={buttonVariants({ variant: "outline" })}>
                Kembali ke daftar
              </Link>
            </div>
          </div>
        ) : (
          <div aria-live="polite">
            <h1 className="text-3xl font-bold">
              {jobStatus === "completed" ? "Modul siap" : "Sedang menyusun modul"}
            </h1>
            <p className="mt-2 text-ink-soft">
              {topic} · Kelas {gradeLevel} · {subject}
            </p>
            <div className="mt-7">
              <GenerationProgress status={jobStatus} />
            </div>
            {jobError && jobStatus !== "completed" && (
              <p className="mt-5 text-sm text-ink-soft">{jobError}</p>
            )}
            {jobStatus === "completed" ? (
              <p className="mt-6 text-ink-soft">Membuka modul...</p>
            ) : (
              <p className="mt-6 font-hand text-xl text-ink-soft">
                Anda boleh menutup halaman ini. Modul tetap tersimpan di daftar.
              </p>
            )}
          </div>
        )}
      </Sheet>
    </div>
  );
}
