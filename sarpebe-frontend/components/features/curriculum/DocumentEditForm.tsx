"use client";

import { useState } from "react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Label } from "@/components/ui/label";
import { Notice } from "@/components/ui/notice";
import { Select } from "@/components/ui/select";
import { useUpdateCurriculumDocument } from "@/lib/hooks/useCurriculum";
import { DOCUMENT_TYPE_OPTIONS } from "@/lib/utils/curriculum";
import { getErrorMessage } from "@/lib/utils/errors";
import { faseForGrade } from "@/lib/utils/fase";
import { normalizeLabel } from "@/lib/utils/formatters";
import { curriculumEditSchema, zodFieldErrors, type CurriculumEditInput } from "@/lib/utils/validators";
import type { CurriculumDocument, DocumentType } from "@/types/curriculum";

type FieldName = keyof CurriculumEditInput;

interface DocumentEditFormProps {
  document: CurriculumDocument;
  onDone: () => void;
}

export function DocumentEditForm({ document, onDone }: DocumentEditFormProps) {
  const update = useUpdateCurriculumDocument();

  const [title, setTitle] = useState(document.title);
  const [documentType, setDocumentType] = useState<DocumentType>(document.document_type);
  const [gradeLevel, setGradeLevel] = useState(document.grade_level ?? "");
  const [subject, setSubject] = useState(document.subject ?? "");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [error, setError] = useState<string | null>(null);

  const fase = faseForGrade(gradeLevel);
  const reprocesses =
    normalizeLabel(gradeLevel) !== normalizeLabel(document.grade_level ?? "") ||
    normalizeLabel(subject) !== normalizeLabel(document.subject ?? "");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const parsed = curriculumEditSchema.safeParse({
      title,
      document_type: documentType,
      grade_level: gradeLevel,
      subject,
    });
    if (!parsed.success) {
      setFieldErrors(zodFieldErrors<FieldName>(parsed.error));
      return;
    }
    setFieldErrors({});

    const changes: Partial<CurriculumEditInput> = {};
    if (parsed.data.title !== document.title) changes.title = parsed.data.title;
    if (parsed.data.document_type !== document.document_type) changes.document_type = parsed.data.document_type;
    if (normalizeLabel(parsed.data.grade_level) !== normalizeLabel(document.grade_level ?? "")) {
      changes.grade_level = parsed.data.grade_level;
    }
    if (normalizeLabel(parsed.data.subject) !== normalizeLabel(document.subject ?? "")) {
      changes.subject = parsed.data.subject;
    }
    if (Object.keys(changes).length === 0) {
      onDone();
      return;
    }

    try {
      await update.mutateAsync({ id: document.id, changes });
      onDone();
    } catch (err) {
      setError(getErrorMessage(err, "Perubahan belum bisa disimpan. Coba lagi."));
    }
  };

  const idPrefix = `edit-${document.id}`;
  const isSaving = update.isPending;

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4 rounded-sm border border-rule bg-wash p-4 sm:p-5">
      <Field
        id={`${idPrefix}-title`}
        label="Judul"
        maxLength={255}
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        disabled={isSaving}
        error={fieldErrors.title}
      />

      <div className="space-y-1.5">
        <Label htmlFor={`${idPrefix}-type`}>Jenis dokumen</Label>
        <Select
          id={`${idPrefix}-type`}
          value={documentType}
          onChange={(e) => setDocumentType(e.target.value as DocumentType)}
          disabled={isSaving}
        >
          {DOCUMENT_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          id={`${idPrefix}-grade`}
          label="Kelas"
          maxLength={20}
          value={gradeLevel}
          onChange={(e) => setGradeLevel(e.target.value)}
          disabled={isSaving}
          error={fieldErrors.grade_level}
          hint={
            fase ? (
              <span className="inline-flex items-center gap-2">
                <FaseTag grade={gradeLevel} /> mencakup {fase.grades}
              </span>
            ) : (
              "Tulis angka kelasnya saja."
            )
          }
        />
        <Field
          id={`${idPrefix}-subject`}
          label="Mata pelajaran"
          maxLength={100}
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={isSaving}
          error={fieldErrors.subject}
        />
      </div>

      {reprocesses && (
        <Notice tone="info">
          <p>Kelas dan mata pelajaran ikut menentukan pencarian. Dokumen akan dibaca dan diindeks ulang setelah disimpan.</p>
        </Notice>
      )}

      {error && (
        <Notice tone="error">
          <p>{error}</p>
        </Notice>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? "Menyimpan..." : "Simpan perubahan"}
        </Button>
        <Button type="button" variant="outline" onClick={onDone} disabled={isSaving}>
          Batal
        </Button>
      </div>
    </form>
  );
}
