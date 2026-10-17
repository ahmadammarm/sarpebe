"use client";

import { useState } from "react";
import { FileUp } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Sheet } from "@/components/brand/Sheet";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Label } from "@/components/ui/label";
import { Notice } from "@/components/ui/notice";
import { Select } from "@/components/ui/select";
import { useUploadCurriculumDocument } from "@/lib/hooks/useCurriculum";
import { getErrorMessage } from "@/lib/utils/errors";
import { faseForGrade } from "@/lib/utils/fase";
import { curriculumUploadSchema, MAX_UPLOAD_MB, zodFieldErrors } from "@/lib/utils/validators";
import type { DocumentType } from "@/types/curriculum";

type FieldName = "grade_level" | "subject" | "document_type" | "file";

const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "CP", label: "Capaian Pembelajaran (CP)" },
  { value: "ATP", label: "Alur Tujuan Pembelajaran (ATP)" },
  { value: "BUKU_GURU", label: "Buku Guru" },
];

function formatSize(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadForm() {
  const upload = useUploadCurriculumDocument();

  const [file, setFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [gradeLevel, setGradeLevel] = useState("");
  const [subject, setSubject] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>("CP");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const fase = faseForGrade(gradeLevel);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    const parsed = curriculumUploadSchema.safeParse({
      file,
      grade_level: gradeLevel,
      subject,
      document_type: documentType,
    });
    if (!parsed.success) {
      setFieldErrors(zodFieldErrors<FieldName>(parsed.error));
      return;
    }
    setFieldErrors({});

    try {
      await upload.mutateAsync(parsed.data);
      setFile(null);
      setFileInputKey((key) => key + 1);
      setGradeLevel("");
      setSubject("");
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err, "Dokumen belum bisa diunggah. Coba lagi."));
    }
  };

  const isUploading = upload.isPending;

  return (
    <Sheet margin className="py-8 pr-6 sm:pr-10">
      <h2 className="text-2xl font-bold">Unggah dokumen</h2>
      <p className="mt-2 max-w-xl text-ink-soft">
        Satu dokumen berlaku untuk satu kelas dan satu mata pelajaran. Guru hanya mendapat rujukan dari dokumen
        yang labelnya cocok dengan yang mereka ketik.
      </p>

      <form onSubmit={handleSubmit} className="mt-7 space-y-5" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="documentType">Jenis dokumen</Label>
          <Select
            id="documentType"
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value as DocumentType)}
            disabled={isUploading}
          >
            {DOCUMENT_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field
            id="grade"
            label="Kelas"
            placeholder="9"
            maxLength={20}
            value={gradeLevel}
            onChange={(e) => setGradeLevel(e.target.value)}
            disabled={isUploading}
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
            id="subject"
            label="Mata pelajaran"
            placeholder="IPS"
            maxLength={100}
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isUploading}
            error={fieldErrors.subject}
            hint="Huruf besar-kecil tidak berpengaruh."
          />
        </div>

        <Field
          key={fileInputKey}
          id="pdf"
          label="File PDF"
          type="file"
          accept=".pdf,application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          disabled={isUploading}
          error={fieldErrors.file}
          hint={file ? `${file.name} (${formatSize(file.size)})` : `PDF, maksimal ${MAX_UPLOAD_MB} MB.`}
        />

        {error && (
          <Notice tone="error">
            <p>{error}</p>
          </Notice>
        )}

        {success && (
          <Notice tone="success">
            <p>Dokumen terunggah. Teksnya sedang dibaca dan diindeks; statusnya akan berubah di daftar di bawah.</p>
          </Notice>
        )}

        <Button type="submit" size="lg" disabled={isUploading}>
          <FileUp aria-hidden />
          {isUploading ? "Mengunggah..." : "Unggah dan indeks"}
        </Button>
      </form>
    </Sheet>
  );
}
