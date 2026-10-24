"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Sheet } from "@/components/brand/Sheet";
import { Button, buttonVariants } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Label } from "@/components/ui/label";
import { Notice } from "@/components/ui/notice";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { GenerationProgress } from "@/components/features/lesson-plans/GenerationProgress";
import { useCreateLessonPlan } from "@/lib/hooks/useLessonPlans";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import { useQuota } from "@/lib/hooks/useUsers";
import { getErrorMessage } from "@/lib/utils/errors";
import { formatDateTime } from "@/lib/utils/formatters";
import { describeFailure } from "@/lib/utils/lesson-plan";
import { faseForGrade } from "@/lib/utils/fase";
import { MAX_CLASS_NOTES, lessonPlanCreateSchema, zodFieldErrors } from "@/lib/utils/validators";
import { TEACHING_MODELS, type TeachingModel } from "@/types/lesson-plan";

type FieldName =
  | "grade_level"
  | "subject"
  | "topic"
  | "meeting_count"
  | "minutes_per_meeting"
  | "teaching_model"
  | "class_notes";

export default function NewLessonPlanPage() {
  const router = useRouter();
  const createPlan = useCreateLessonPlan();
  const { data: quota } = useQuota();
  const quotaReached = quota?.remaining === 0;

  const [gradeLevel, setGradeLevel] = useState("");
  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [meetingCount, setMeetingCount] = useState("1");
  const [minutesPerMeeting, setMinutesPerMeeting] = useState("80");
  const [teachingModel, setTeachingModel] = useState<TeachingModel>("otomatis");
  const [classNotes, setClassNotes] = useState("");

  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [createdPlanId, setCreatedPlanId] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    status: jobStatus,
    stage,
    isDone,
    error: jobError,
    errorCode: jobErrorCode,
    connectionError,
  } = useJobStatus(activeJobId);
  const fase = faseForGrade(gradeLevel);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const parsed = lessonPlanCreateSchema.safeParse({
      grade_level: gradeLevel,
      subject,
      topic,
      meeting_count: meetingCount.trim() === "" ? Number.NaN : Number(meetingCount),
      minutes_per_meeting: minutesPerMeeting.trim() === "" ? Number.NaN : Number(minutesPerMeeting),
      teaching_model: teachingModel,
      class_notes: classNotes,
    });
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
  const failure = describeFailure(jobError, jobErrorCode);

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

              <div className="grid gap-5 sm:grid-cols-2">
                <Field
                  id="meetingCount"
                  label="Jumlah pertemuan"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={6}
                  value={meetingCount}
                  onChange={(e) => setMeetingCount(e.target.value)}
                  error={fieldErrors.meeting_count}
                  hint="1 sampai 6 pertemuan."
                />
                <Field
                  id="minutesPerMeeting"
                  label="Menit per pertemuan"
                  type="number"
                  inputMode="numeric"
                  min={20}
                  max={240}
                  value={minutesPerMeeting}
                  onChange={(e) => setMinutesPerMeeting(e.target.value)}
                  error={fieldErrors.minutes_per_meeting}
                  hint="Misalnya 2 jam pelajaran x 40 menit = 80."
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="teachingModel">Model pembelajaran</Label>
                <Select
                  id="teachingModel"
                  value={teachingModel}
                  onChange={(e) => setTeachingModel(e.target.value as TeachingModel)}
                >
                  {TEACHING_MODELS.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-baseline justify-between gap-3">
                  <Label htmlFor="classNotes">Catatan kelas (opsional)</Label>
                  <span
                    className="text-sm text-ink-soft tabular-nums"
                    aria-live="off"
                  >
                    {classNotes.length}/{MAX_CLASS_NOTES}
                  </span>
                </div>
                <Textarea
                  id="classNotes"
                  rows={3}
                  maxLength={MAX_CLASS_NOTES}
                  placeholder="Misalnya: 32 siswa, belum ada proyektor, banyak yang suka diskusi."
                  value={classNotes}
                  onChange={(e) => setClassNotes(e.target.value)}
                  aria-invalid={Boolean(fieldErrors.class_notes)}
                  aria-describedby={fieldErrors.class_notes ? "classNotes-error" : undefined}
                />
                {fieldErrors.class_notes && (
                  <p id="classNotes-error" className="text-sm font-medium text-margin-text">
                    {fieldErrors.class_notes}
                  </p>
                )}
              </div>

              {errorMsg && (
                <Notice tone="error">
                  <p>{errorMsg}</p>
                </Notice>
              )}

              {quota && !quota.unlimited && (
                quotaReached ? (
                  <Notice tone="info">
                    <p>
                      Batas {quota.limit} modul dalam 24 jam terakhir sudah tercapai.
                      {quota.resets_at && ` Anda bisa menyusun lagi mulai ${formatDateTime(quota.resets_at)}.`}
                    </p>
                  </Notice>
                ) : (
                  <p className="text-sm text-ink-soft" aria-live="polite">
                    Sisa {quota.remaining} dari {quota.limit} modul dalam 24 jam terakhir.
                  </p>
                )
              )}

              <Button type="submit" size="lg" className="w-full sm:w-auto" disabled={createPlan.isPending || quotaReached}>
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
              <GenerationProgress status={jobStatus} stage={stage} />
            </div>
            {connectionError && jobStatus !== "completed" && (
              <p className="mt-5 text-sm text-ink-soft">{connectionError}</p>
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
