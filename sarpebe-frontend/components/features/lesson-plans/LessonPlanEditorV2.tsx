"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Download, FileText, Plus, Save, Trash2 } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Mark } from "@/components/brand/Mark";
import { Sheet } from "@/components/brand/Sheet";
import { Button } from "@/components/ui/button";
import { EditableTable } from "@/components/ui/editable-table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Notice } from "@/components/ui/notice";
import { Textarea } from "@/components/ui/textarea";
import { useDownloadLessonPlan, useUpdateLessonPlan } from "@/lib/hooks/useLessonPlans";
import type { ExportFormat } from "@/lib/api/lesson-plans";
import { getErrorMessage } from "@/lib/utils/errors";
import { cn } from "@/lib/utils";
import type {
  AssessmentItem,
  GlossaryItem,
  LessonPlanContentV2,
  LessonPlanV2,
  Reference,
  Table,
} from "@/types/lesson-plan";

const ASSESSMENT_KINDS = [
  { key: "diagnostic", label: "Asesmen diagnostik" },
  { key: "formative", label: "Asesmen formatif" },
  { key: "summative", label: "Asesmen sumatif" },
] as const;

/** Drops blank lines and empty entries, so what is saved is what a reader would see. */
function tidy(content: LessonPlanContentV2): LessonPlanContentV2 {
  const lines = (items: string[]) => items.map((item) => item.trim()).filter(Boolean);
  const dropBlankRows = (table: Table): Table => ({
    ...table,
    rows: table.rows.filter((row) => row.some((cell) => cell.trim())),
  });

  return {
    ...content,
    initial_competencies: lines(content.initial_competencies),
    facilities: lines(content.facilities),
    meaningful_understanding: lines(content.meaningful_understanding),
    trigger_questions: lines(content.trigger_questions),
    preparation: lines(content.preparation),
    enrichment: lines(content.enrichment),
    remedial: lines(content.remedial),
    learning_objectives: content.learning_objectives.filter((item) => item.text.trim()),
    meetings: content.meetings.map((meeting) => ({ ...meeting, activities: dropBlankRows(meeting.activities) })),
    assessment: {
      ...content.assessment,
      overview: dropBlankRows(content.assessment.overview),
      rubric: dropBlankRows(content.assessment.rubric),
    },
    reflection: {
      teacher: lines(content.reflection.teacher),
      students: lines(content.reflection.students),
    },
    attachments: {
      ...content.attachments,
      worksheet: { ...content.attachments.worksheet, tasks: lines(content.attachments.worksheet.tasks) },
      glossary: content.attachments.glossary.filter((item) => item.term.trim() || item.definition.trim()),
    },
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
      <div className="mt-4 space-y-5">{children}</div>
    </section>
  );
}

/** One entry per line, edited as plain text. */
function LinesField({
  id,
  label,
  help,
  value,
  onChange,
  rows = 4,
}: {
  id: string;
  label: string;
  help?: string;
  value: string[];
  onChange: (value: string[]) => void;
  rows?: number;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {help && <p className="text-sm text-ink-soft">{help}</p>}
      <Textarea id={id} lined rows={rows} value={value.join("\n")} onChange={(e) => onChange(e.target.value.split("\n"))} />
    </div>
  );
}

function TextField({
  id,
  label,
  value,
  onChange,
  multiline = false,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {multiline ? (
        <Textarea id={id} rows={4} value={value} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <Input id={id} value={value} onChange={(e) => onChange(e.target.value)} />
      )}
    </div>
  );
}

function referenceLabel(reference: Reference): string {
  const pages =
    reference.page == null
      ? ""
      : reference.page_end && reference.page_end !== reference.page
        ? `, hlm. ${reference.page}-${reference.page_end}`
        : `, hlm. ${reference.page}`;
  return `${reference.document_title}${pages}`;
}

/** Where an objective comes from; a design of the model's own gets a plain label instead. */
function SourceChips({ ids, grounded, references }: { ids: string[]; grounded: boolean; references: Reference[] }) {
  const known = ids
    .map((sourceId) => references.find((reference) => reference.id === sourceId))
    .filter((reference): reference is Reference => Boolean(reference));

  if (known.length === 0) {
    return (
      <p className="text-sm text-ink-soft">
        {grounded ? "Sumber tidak tercatat." : "Rancangan model, bukan kutipan CP. Periksa sebelum dipakai."}
      </p>
    );
  }

  return (
    <ul className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
      {known.map((reference) => (
        <li key={reference.id}>
          <Mark>
            {reference.id} · {referenceLabel(reference)}
          </Mark>
        </li>
      ))}
    </ul>
  );
}

export function LessonPlanEditorV2({ plan }: { plan: LessonPlanV2 }) {
  const initial = plan.generated_content as LessonPlanContentV2;
  const [content, setContent] = useState<LessonPlanContentV2>(initial);
  const [saved, setSaved] = useState<LessonPlanContentV2>(initial);
  const [justSaved, setJustSaved] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const updatePlan = useUpdateLessonPlan(plan.id);
  const download = useDownloadLessonPlan();

  const dirty = JSON.stringify(content) !== JSON.stringify(saved);

  // Warn before the tab closes with edits that were never saved.
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const change = (update: (previous: LessonPlanContentV2) => LessonPlanContentV2) => {
    setJustSaved(false);
    setContent(update);
  };

  const setField = <K extends keyof LessonPlanContentV2>(field: K, value: LessonPlanContentV2[K]) =>
    change((previous) => ({ ...previous, [field]: value }));

  const handleSave = async () => {
    try {
      setErrorMsg(null);
      const tidied = tidy(content);
      const updated = await updatePlan.mutateAsync(tidied);
      const stored = (updated.generated_content as LessonPlanContentV2 | null) ?? tidied;
      setContent(stored);
      setSaved(stored);
      setJustSaved(true);
    } catch (err) {
      setErrorMsg(getErrorMessage(err, "Perubahan belum tersimpan. Coba lagi."));
    }
  };

  const handleDownload = async (format: ExportFormat) => {
    try {
      setErrorMsg(null);
      await download.mutateAsync({ id: plan.id, topic: content.title || plan.topic, format });
    } catch (err) {
      setErrorMsg(getErrorMessage(err, `${format === "pdf" ? "PDF" : "Dokumen Word"} belum bisa diunduh. Coba lagi.`));
    }
  };

  const { identity, assessment, attachments } = content;

  const setAssessmentItem = (kind: (typeof ASSESSMENT_KINDS)[number]["key"], patch: Partial<AssessmentItem>) =>
    change((previous) => ({
      ...previous,
      assessment: { ...previous.assessment, [kind]: { ...previous.assessment[kind], ...patch } },
    }));

  const setGlossary = (glossary: GlossaryItem[]) =>
    change((previous) => ({ ...previous, attachments: { ...previous.attachments, glossary } }));

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
          <h1 className="mt-1 text-2xl font-bold leading-tight [overflow-wrap:anywhere] sm:text-4xl">
            {content.title || plan.topic}
          </h1>
        </div>

        <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto sm:items-center">
          <Button variant="outline" onClick={() => handleDownload("pdf")} disabled={download.isPending}>
            <Download aria-hidden />
            {download.isPending && download.variables?.format === "pdf" ? "Menyiapkan..." : "Unduh PDF"}
          </Button>
          <Button variant="outline" onClick={() => handleDownload("docx")} disabled={download.isPending}>
            <FileText aria-hidden />
            {download.isPending && download.variables?.format === "docx" ? "Menyiapkan..." : "Unduh Word"}
          </Button>
          <Button onClick={handleSave} disabled={!dirty || updatePlan.isPending} className="col-span-2 sm:col-auto">
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

      {content.warnings.length > 0 && (
        <Notice tone="info">
          <p>Periksa bagian ini sebelum modul dipakai:</p>
          <ul className="list-disc space-y-1 pl-5 font-normal">
            {content.warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </Notice>
      )}

      <Sheet margin className="py-8 pr-5 sm:pr-10">
        <Section id="identitas" title="Informasi umum">
          <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
            {[
              ["Mata pelajaran", identity.subject],
              ["Kelas", identity.fase ? `${identity.grade_level} (Fase ${identity.fase})` : identity.grade_level],
              ["Topik", identity.topic],
              ["Alokasi waktu", `${identity.meetings} pertemuan x ${identity.minutes_per_meeting} menit`],
            ].map(([term, detail]) => (
              <div key={term}>
                <dt className="text-ink-soft">{term}</dt>
                <dd className="font-semibold [overflow-wrap:anywhere]">{detail}</dd>
              </div>
            ))}
          </dl>

          <TextField id="title" label="Judul modul" value={content.title} onChange={(value) => setField("title", value)} />
          <LinesField
            id="initial-competencies"
            label="Kompetensi awal"
            help="Satu kompetensi per baris."
            value={content.initial_competencies}
            onChange={(value) => setField("initial_competencies", value)}
          />
          <LinesField
            id="facilities"
            label="Sarana dan prasarana"
            help="Satu item per baris."
            value={content.facilities}
            onChange={(value) => setField("facilities", value)}
          />
          <TextField
            id="target-students"
            label="Target peserta didik"
            multiline
            value={content.target_students}
            onChange={(value) => setField("target_students", value)}
          />

          <div className="space-y-3">
            <h3 className="text-base font-bold">Profil Pelajar Pancasila</h3>
            <ul className="space-y-3">
              {content.pancasila_profile.map((item, index) => (
                <li key={item.dimension} className="space-y-1.5">
                  <Label htmlFor={`pancasila-${index}`}>{item.dimension}</Label>
                  <Textarea
                    id={`pancasila-${index}`}
                    rows={2}
                    value={item.how}
                    onChange={(e) =>
                      change((previous) => ({
                        ...previous,
                        pancasila_profile: previous.pancasila_profile.map((entry, i) =>
                          i === index ? { ...entry, how: e.target.value } : entry
                        ),
                      }))
                    }
                  />
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <h3 className="text-base font-bold">Model pembelajaran</h3>
            <TextField
              id="model-name"
              label="Model"
              value={content.learning_model.name}
              onChange={(value) => setField("learning_model", { ...content.learning_model, name: value })}
            />
            <TextField
              id="model-rationale"
              label="Alasan memilih model ini"
              multiline
              value={content.learning_model.rationale}
              onChange={(value) => setField("learning_model", { ...content.learning_model, rationale: value })}
            />
          </div>
        </Section>

        <Section id="komponen-inti" title="Komponen inti">
          <div className="space-y-3">
            <h3 className="text-base font-bold">Tujuan pembelajaran</h3>
            <ul className="space-y-4">
              {content.learning_objectives.map((objective, index) => (
                <li
                  key={index}
                  className="space-y-2 animate-in fade-in slide-in-from-top-1 duration-200"
                >
                  <div className="flex items-start gap-2">
                    <div className="min-w-0 flex-1 space-y-1.5">
                      <Label htmlFor={`objective-${index}`}>Tujuan {index + 1}</Label>
                      <Textarea
                        id={`objective-${index}`}
                        rows={2}
                        value={objective.text}
                        onChange={(e) =>
                          change((previous) => ({
                            ...previous,
                            learning_objectives: previous.learning_objectives.map((entry, i) =>
                              i === index ? { ...entry, text: e.target.value } : entry
                            ),
                          }))
                        }
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      className="mt-7 text-ink-soft hover:bg-margin-wash hover:text-margin-text"
                      aria-label={`Hapus tujuan ${index + 1}`}
                      onClick={() =>
                        change((previous) => ({
                          ...previous,
                          learning_objectives: previous.learning_objectives.filter((_, i) => i !== index),
                        }))
                      }
                    >
                      <Trash2 aria-hidden />
                    </Button>
                  </div>
                  <SourceChips ids={objective.source_ids} grounded={objective.grounded} references={content.references} />
                </li>
              ))}
            </ul>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                setField("learning_objectives", [
                  ...content.learning_objectives,
                  { text: "", source_ids: [], grounded: false },
                ])
              }
            >
              <Plus aria-hidden />
              Tambah tujuan
            </Button>
          </div>

          <LinesField
            id="meaningful-understanding"
            label="Pemahaman bermakna"
            help="Satu butir per baris."
            value={content.meaningful_understanding}
            onChange={(value) => setField("meaningful_understanding", value)}
          />
          <LinesField
            id="trigger-questions"
            label="Pertanyaan pemantik"
            help="Satu pertanyaan per baris."
            value={content.trigger_questions}
            onChange={(value) => setField("trigger_questions", value)}
          />
          <LinesField
            id="preparation"
            label="Persiapan pembelajaran"
            help="Satu langkah per baris."
            value={content.preparation}
            onChange={(value) => setField("preparation", value)}
          />
        </Section>

        <Section
          id="kegiatan"
          title="Kegiatan pembelajaran"
          help="Jumlah waktu semua kegiatan dalam satu pertemuan sebaiknya sama dengan menit per pertemuan."
        >
          {content.meetings.map((meeting, index) => {
            const total = meeting.activities.rows.reduce((sum, row) => sum + (Number.parseInt(row[1] ?? "", 10) || 0), 0);
            const matches = total === identity.minutes_per_meeting;

            return (
              <div key={meeting.number} className="space-y-3">
                <h3 className="text-base font-bold">Pertemuan {meeting.number}</h3>
                <TextField
                  id={`meeting-title-${index}`}
                  label="Fokus pertemuan"
                  value={meeting.title}
                  onChange={(value) =>
                    change((previous) => ({
                      ...previous,
                      meetings: previous.meetings.map((entry, i) => (i === index ? { ...entry, title: value } : entry)),
                    }))
                  }
                />
                <EditableTable
                  id={`meeting-${index}`}
                  rowName="kegiatan"
                  table={meeting.activities}
                  onChange={(activities) =>
                    change((previous) => ({
                      ...previous,
                      meetings: previous.meetings.map((entry, i) => (i === index ? { ...entry, activities } : entry)),
                    }))
                  }
                />
                <p className={cn("text-sm", matches ? "text-tick" : "font-medium text-margin-text")}>
                  Total waktu {total} menit dari {identity.minutes_per_meeting} menit
                  {matches ? "." : ". Sesuaikan kolom waktu."}
                </p>
              </div>
            );
          })}
        </Section>

        <Section id="asesmen" title="Asesmen">
          {ASSESSMENT_KINDS.map(({ key, label }) => (
            <div key={key} className="space-y-3">
              <h3 className="text-base font-bold">{label}</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <TextField
                  id={`${key}-technique`}
                  label="Teknik"
                  value={assessment[key].technique}
                  onChange={(value) => setAssessmentItem(key, { technique: value })}
                />
                <TextField
                  id={`${key}-instrument`}
                  label="Instrumen"
                  value={assessment[key].instrument}
                  onChange={(value) => setAssessmentItem(key, { instrument: value })}
                />
              </div>
              <TextField
                id={`${key}-description`}
                label="Penjelasan"
                multiline
                value={assessment[key].description}
                onChange={(value) => setAssessmentItem(key, { description: value })}
              />
            </div>
          ))}

          <div className="space-y-3">
            <h3 className="text-base font-bold">{assessment.overview.caption}</h3>
            <EditableTable
              id="overview"
              rowName="asesmen"
              table={assessment.overview}
              onChange={(overview) => change((previous) => ({ ...previous, assessment: { ...previous.assessment, overview } }))}
            />
          </div>

          <div className="space-y-3">
            <h3 className="text-base font-bold">{assessment.rubric.caption}</h3>
            <EditableTable
              id="rubric"
              rowName="kriteria"
              table={assessment.rubric}
              onChange={(rubric) => change((previous) => ({ ...previous, assessment: { ...previous.assessment, rubric } }))}
            />
          </div>
        </Section>

        <Section id="pengayaan" title="Pengayaan dan remedial">
          <LinesField
            id="enrichment"
            label="Pengayaan"
            help="Satu kegiatan per baris."
            value={content.enrichment}
            onChange={(value) => setField("enrichment", value)}
          />
          <LinesField
            id="remedial"
            label="Remedial"
            help="Satu kegiatan per baris."
            value={content.remedial}
            onChange={(value) => setField("remedial", value)}
          />
        </Section>

        <Section id="refleksi" title="Refleksi">
          <LinesField
            id="reflection-teacher"
            label="Untuk guru"
            help="Satu pertanyaan per baris."
            value={content.reflection.teacher}
            onChange={(value) => setField("reflection", { ...content.reflection, teacher: value })}
          />
          <LinesField
            id="reflection-students"
            label="Untuk peserta didik"
            help="Satu pertanyaan per baris."
            value={content.reflection.students}
            onChange={(value) => setField("reflection", { ...content.reflection, students: value })}
          />
        </Section>

        <Section id="lampiran" title="Lampiran">
          <div className="space-y-3">
            <h3 className="text-base font-bold">Lembar kerja peserta didik</h3>
            <TextField
              id="worksheet-title"
              label="Judul LKPD"
              value={attachments.worksheet.title}
              onChange={(value) =>
                setField("attachments", { ...attachments, worksheet: { ...attachments.worksheet, title: value } })
              }
            />
            <TextField
              id="worksheet-instructions"
              label="Petunjuk"
              multiline
              value={attachments.worksheet.instructions}
              onChange={(value) =>
                setField("attachments", { ...attachments, worksheet: { ...attachments.worksheet, instructions: value } })
              }
            />
            <LinesField
              id="worksheet-tasks"
              label="Tugas"
              help="Satu tugas per baris."
              value={attachments.worksheet.tasks}
              onChange={(value) =>
                setField("attachments", { ...attachments, worksheet: { ...attachments.worksheet, tasks: value } })
              }
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reading-material">Bahan bacaan</Label>
            <Textarea
              id="reading-material"
              rows={8}
              value={attachments.reading_material}
              onChange={(e) => setField("attachments", { ...attachments, reading_material: e.target.value })}
            />
          </div>

          <div className="space-y-3">
            <h3 className="text-base font-bold">Glosarium</h3>
            <ul className="space-y-3">
              {attachments.glossary.map((item, index) => (
                <li key={index} className="grid gap-3 sm:grid-cols-[12rem_minmax(0,1fr)_auto] sm:items-start">
                  <div className="space-y-1.5">
                    <Label htmlFor={`glossary-term-${index}`}>Istilah {index + 1}</Label>
                    <Input
                      id={`glossary-term-${index}`}
                      value={item.term}
                      onChange={(e) =>
                        setGlossary(attachments.glossary.map((entry, i) => (i === index ? { ...entry, term: e.target.value } : entry)))
                      }
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor={`glossary-definition-${index}`}>Pengertian</Label>
                    <Textarea
                      id={`glossary-definition-${index}`}
                      rows={2}
                      value={item.definition}
                      onChange={(e) =>
                        setGlossary(
                          attachments.glossary.map((entry, i) => (i === index ? { ...entry, definition: e.target.value } : entry))
                        )
                      }
                    />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    className="text-ink-soft hover:bg-margin-wash hover:text-margin-text sm:mt-7"
                    aria-label={`Hapus istilah ${index + 1}`}
                    onClick={() => setGlossary(attachments.glossary.filter((_, i) => i !== index))}
                  >
                    <Trash2 aria-hidden />
                  </Button>
                </li>
              ))}
            </ul>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setGlossary([...attachments.glossary, { term: "", definition: "" }])}
            >
              <Plus aria-hidden />
              Tambah istilah
            </Button>
          </div>
        </Section>

        <Section id="rujukan" title="Sumber rujukan">
          {content.references.length > 0 ? (
            <>
              <ul className="space-y-2">
                {content.references.map((reference, index) => (
                  <li key={reference.id} className="leading-7">
                    <Mark draw="view" delay={index * 140}>
                      {reference.id} · {referenceLabel(reference)}
                    </Mark>
                    {reference.heading && <span className="text-ink-soft"> — {reference.heading}</span>}
                  </li>
                ))}
              </ul>
              <p className="font-hand text-xl text-ink-soft">
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
