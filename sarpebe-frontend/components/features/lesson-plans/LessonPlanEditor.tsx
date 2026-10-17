"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, Plus, Save, Trash2 } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Mark } from "@/components/brand/Mark";
import { Sheet } from "@/components/brand/Sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Notice } from "@/components/ui/notice";
import { Textarea } from "@/components/ui/textarea";
import { useDownloadLessonPlanPdf, useUpdateLessonPlan } from "@/lib/hooks/useLessonPlans";
import { getErrorMessage } from "@/lib/utils/errors";
import type { LessonActivity, LessonPlanContent, LessonPlanV1 } from "@/types/lesson-plan";

interface LessonPlanEditorProps {
  plan: LessonPlanV1;
}

/** Drops blank lines and empty activities, so what is saved is what a reader would see. */
function tidy(content: LessonPlanContent): LessonPlanContent {
  const lines = (items?: string[]) => items?.map((item) => item.trim()).filter(Boolean);
  return {
    ...content,
    objectives: lines(content.objectives),
    materials: lines(content.materials),
    activities: content.activities?.filter((a) => a.duration.trim() || a.description.trim()),
  };
}

function Section({
  id,
  title,
  help,
  children,
}: {
  id: string;
  title: string;
  help?: string;
  children: React.ReactNode;
}) {
  return (
    <section aria-labelledby={id} className="border-t border-rule py-7 first:border-t-0 first:pt-0">
      <h2 id={id} className="text-xl font-bold">
        {title}
      </h2>
      {help && <p className="mt-1 text-sm text-ink-soft">{help}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function LessonPlanEditor({ plan }: LessonPlanEditorProps) {
  const initial = plan.generated_content ?? {};
  const [content, setContent] = useState<LessonPlanContent>(initial);
  const [saved, setSaved] = useState<LessonPlanContent>(initial);
  const [justSaved, setJustSaved] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const updatePlan = useUpdateLessonPlan(plan.id);
  const downloadPdf = useDownloadLessonPlanPdf();

  const dirty = JSON.stringify(content) !== JSON.stringify(saved);

  // Warn before the tab closes with edits that were never saved.
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const updateField = <K extends keyof LessonPlanContent>(field: K, value: LessonPlanContent[K]) => {
    setJustSaved(false);
    setContent((prev) => ({ ...prev, [field]: value }));
  };

  const updateActivity = (index: number, patch: Partial<LessonActivity>) => {
    const activities = [...(content.activities ?? [])];
    activities[index] = { ...activities[index], ...patch };
    updateField("activities", activities);
  };

  const handleSave = async () => {
    try {
      setErrorMsg(null);
      const tidied = tidy(content);
      const updated = await updatePlan.mutateAsync(tidied);
      const stored = (updated.generated_content as LessonPlanContent | null) ?? tidied;
      setContent(stored);
      setSaved(stored);
      setJustSaved(true);
    } catch (err) {
      setErrorMsg(getErrorMessage(err, "Perubahan belum tersimpan. Coba lagi."));
    }
  };

  const handleDownload = async () => {
    try {
      setErrorMsg(null);
      await downloadPdf.mutateAsync({ id: plan.id, topic: content.title || plan.topic });
    } catch (err) {
      setErrorMsg(getErrorMessage(err, "PDF belum bisa diunduh. Coba lagi."));
    }
  };

  const citations = content.citations ?? [];

  return (
    <div className="space-y-6">
      <Link
        href="/lesson-plans"
        className="inline-flex items-center gap-1.5 rounded-sm text-sm font-medium text-ink-soft outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/40"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Modul ajar saya
      </Link>

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-soft">
            <span>Kelas {plan.grade_level}</span>
            <FaseTag grade={plan.grade_level} />
            <span aria-hidden>·</span>
            <span>{plan.subject}</span>
          </p>
          <h1 className="mt-1 text-2xl font-bold leading-tight [overflow-wrap:anywhere] sm:text-4xl">{content.title || plan.topic}</h1>
        </div>

        <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:items-center">
          <Button variant="outline" onClick={handleDownload} disabled={downloadPdf.isPending}>
            <Download aria-hidden />
            {downloadPdf.isPending ? "Menyiapkan..." : "Unduh PDF"}
          </Button>
          <Button onClick={handleSave} disabled={!dirty || updatePlan.isPending}>
            <Save aria-hidden />
            {updatePlan.isPending ? "Menyimpan..." : "Simpan perubahan"}
          </Button>
        </div>
      </div>

      <div aria-live="polite" className="min-h-6 text-sm">
        {dirty && (
          <span className="animate-in fade-in slide-in-from-bottom-1 font-medium text-margin-text duration-200">
            Ada perubahan yang belum disimpan.
          </span>
        )}
        {!dirty && justSaved && (
          <span className="animate-in fade-in slide-in-from-bottom-1 font-medium text-tick duration-200">
            Perubahan tersimpan.
          </span>
        )}
      </div>

      {errorMsg && (
        <Notice tone="error">
          <p>{errorMsg}</p>
        </Notice>
      )}

      <Sheet margin className="py-8 pr-5 sm:pr-10">
        <Section id="judul" title="Judul modul">
          <Label htmlFor="title" className="sr-only">
            Judul modul
          </Label>
          <Input
            id="title"
            value={content.title ?? ""}
            onChange={(e) => updateField("title", e.target.value)}
            className="h-12 font-display text-lg font-semibold"
          />
        </Section>

        <Section id="tujuan" title="Tujuan pembelajaran" help="Satu tujuan per baris.">
          <Label htmlFor="objectives" className="sr-only">
            Tujuan pembelajaran
          </Label>
          <Textarea
            id="objectives"
            lined
            rows={6}
            value={(content.objectives ?? []).join("\n")}
            onChange={(e) => updateField("objectives", e.target.value.split("\n"))}
          />
        </Section>

        <Section id="kegiatan" title="Kegiatan pembelajaran" help="Isi lama kegiatan dan apa yang dilakukan.">
          <ul className="space-y-4">
            {(content.activities ?? []).map((activity, index) => (
              <li
                key={index}
                className="grid gap-3 animate-in fade-in slide-in-from-top-1 duration-200 sm:grid-cols-[9rem_minmax(0,1fr)_auto] sm:items-start"
              >
                <div>
                  <Label htmlFor={`activity-duration-${index}`} className="mb-1.5">
                    Durasi
                  </Label>
                  <Input
                    id={`activity-duration-${index}`}
                    placeholder="15 menit"
                    value={activity.duration}
                    onChange={(e) => updateActivity(index, { duration: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor={`activity-description-${index}`} className="mb-1.5">
                    Kegiatan {index + 1}
                  </Label>
                  <Textarea
                    id={`activity-description-${index}`}
                    rows={3}
                    value={activity.description}
                    onChange={(e) => updateActivity(index, { description: e.target.value })}
                  />
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="text-ink-soft hover:bg-margin-wash hover:text-margin-text sm:mt-7"
                  aria-label={`Hapus kegiatan ${index + 1}`}
                  onClick={() =>
                    updateField(
                      "activities",
                      (content.activities ?? []).filter((_, i) => i !== index)
                    )
                  }
                >
                  <Trash2 aria-hidden />
                </Button>
              </li>
            ))}
          </ul>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => updateField("activities", [...(content.activities ?? []), { duration: "", description: "" }])}
          >
            <Plus aria-hidden />
            Tambah kegiatan
          </Button>
        </Section>

        <Section id="media" title="Media dan sumber belajar" help="Satu item per baris.">
          <Label htmlFor="materials" className="sr-only">
            Media dan sumber belajar
          </Label>
          <Textarea
            id="materials"
            lined
            rows={5}
            value={(content.materials ?? []).join("\n")}
            onChange={(e) => updateField("materials", e.target.value.split("\n"))}
          />
        </Section>

        <Section id="asesmen" title="Asesmen" help="Bagaimana Anda mengetahui tujuan sudah tercapai.">
          <Label htmlFor="assessment" className="sr-only">
            Asesmen
          </Label>
          <Textarea
            id="assessment"
            lined
            rows={5}
            value={content.assessment ?? ""}
            onChange={(e) => updateField("assessment", e.target.value)}
          />
        </Section>

        <Section id="rujukan" title="Sumber rujukan">
          {citations.length > 0 ? (
            <>
              <ul className="space-y-2">
                {citations.map((citation, index) => (
                  <li key={index} className="leading-7">
                    <Mark draw="view" delay={index * 140}>
                      {citation}
                    </Mark>
                  </li>
                ))}
              </ul>
              <p className="mt-4 font-hand text-xl text-ink-soft">
                Dicatat otomatis dari dokumen CP yang diunggah, jadi tidak bisa disunting di sini.
              </p>
            </>
          ) : (
            <Notice tone="info">
              <p>Modul ini tidak mencantumkan rujukan. Cocokkan isinya dengan dokumen CP sebelum dipakai.</p>
            </Notice>
          )}
        </Section>
      </Sheet>
    </div>
  );
}
