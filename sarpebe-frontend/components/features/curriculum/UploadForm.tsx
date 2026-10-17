"use client";

import { useState } from "react";
import { useUploadCurriculumDocument } from "@/lib/hooks/useCurriculum";
import { getErrorMessage } from "@/lib/utils/errors";
import { curriculumUploadSchema, zodFieldErrors } from "@/lib/utils/validators";
import type { DocumentType } from "@/types/curriculum";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

type FieldName = "grade_level" | "subject" | "document_type" | "file";

const DOCUMENT_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: "CP", label: "Capaian Pembelajaran (CP)" },
  { value: "ATP", label: "Alur Tujuan Pembelajaran (ATP)" },
  { value: "BUKU_GURU", label: "Buku Guru" },
];

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
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      setError(getErrorMessage(err, "Gagal mengunggah dokumen kurikulum."));
    }
  };

  const isUploading = upload.isPending;

  return (
    <Card className="mb-8 border-slate-200/80 shadow-xs">
      <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
        <CardTitle className="text-lg font-bold text-emerald-950 flex items-center gap-2">
          <UploadCloud className="h-5 w-5 text-emerald-600" />
          Unggah Dokumen Kurikulum (Admin)
        </CardTitle>
        <CardDescription className="text-slate-500 text-xs">
          Unggah file PDF resmi Capaian Pembelajaran (CP) atau Alur Tujuan Pembelajaran (ATP) untuk diindeks ke basis data vektor.
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="grade" className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Tingkat Kelas
              </Label>
              <Input
                id="grade"
                placeholder="Contoh: 10, 11, atau 12"
                value={gradeLevel}
                onChange={(e) => setGradeLevel(e.target.value)}
                disabled={isUploading}
                aria-invalid={Boolean(fieldErrors.grade_level)}
                className="focus-visible:ring-emerald-500"
              />
              {fieldErrors.grade_level && <p className="text-xs text-rose-600">{fieldErrors.grade_level}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="subject" className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Mata Pelajaran
              </Label>
              <Input
                id="subject"
                placeholder="Contoh: Biologi, Matematika"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                disabled={isUploading}
                aria-invalid={Boolean(fieldErrors.subject)}
                className="focus-visible:ring-emerald-500"
              />
              {fieldErrors.subject && <p className="text-xs text-rose-600">{fieldErrors.subject}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="documentType" className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Jenis Dokumen
              </Label>
              <select
                id="documentType"
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value as DocumentType)}
                disabled={isUploading}
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:ring-3 focus-visible:ring-emerald-500/50 disabled:opacity-50"
              >
                {DOCUMENT_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="pdf" className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              File PDF Kurikulum
            </Label>
            <Input
              key={fileInputKey}
              id="pdf"
              type="file"
              accept=".pdf,application/pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              disabled={isUploading}
              aria-invalid={Boolean(fieldErrors.file)}
              className="file:text-emerald-700 file:font-semibold focus-visible:ring-emerald-500"
            />
            {fieldErrors.file && <p className="text-xs text-rose-600">{fieldErrors.file}</p>}
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-sm rounded-xl flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-xl flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              Dokumen berhasil diunggah! Pemrosesan teks dan embedding sedang berjalan di latar belakang.
            </div>
          )}

          <Button type="submit" disabled={isUploading} className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-600/20">
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Mengunggah & Memproses...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                Unggah & Indeks Dokumen
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
