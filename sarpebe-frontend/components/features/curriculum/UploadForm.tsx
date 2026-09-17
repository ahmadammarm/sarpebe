"use client";

import { useState } from "react";
import { uploadCurriculumDocument } from "@/lib/api/curriculum";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

interface UploadFormProps {
  onUploadSuccess: () => void;
}

export function UploadForm({ onUploadSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [gradeLevel, setGradeLevel] = useState("");
  const [subject, setSubject] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !gradeLevel || !subject) {
      setError("Semua field wajib diisi.");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setSuccess(false);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("grade_level", gradeLevel);
      formData.append("subject", subject);

      await uploadCurriculumDocument(formData);
      setFile(null);
      setGradeLevel("");
      setSubject("");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
      onUploadSuccess();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Gagal mengunggah dokumen kurikulum.");
    } finally {
      setIsUploading(false);
    }
  };

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
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                className="focus-visible:ring-emerald-500"
              />
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
                className="focus-visible:ring-emerald-500"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="pdf" className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              File PDF Kurikulum
            </Label>
            <Input
              id="pdf"
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              disabled={isUploading}
              className="file:text-emerald-700 file:font-semibold focus-visible:ring-emerald-500"
            />
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
