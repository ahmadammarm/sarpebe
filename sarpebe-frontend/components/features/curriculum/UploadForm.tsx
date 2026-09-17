"use client";

import { useState } from "react";
import { uploadCurriculumDocument } from "@/lib/api/curriculum";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface UploadFormProps {
  onUploadSuccess: () => void;
}

export function UploadForm({ onUploadSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [gradeLevel, setGradeLevel] = useState("");
  const [subject, setSubject] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !gradeLevel || !subject) {
      setError("Semua field wajib diisi.");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("grade_level", gradeLevel);
      formData.append("subject", subject);

      await uploadCurriculumDocument(formData);
      setFile(null);
      setGradeLevel("");
      setSubject("");
      onUploadSuccess();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Gagal mengunggah dokumen kurikulum.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle>Unggah Dokumen Kurikulum (Admin)</CardTitle>
        <CardDescription>
          Unggah file PDF resmi Capaian Pembelajaran (CP) atau Alur Tujuan Pembelajaran (ATP) untuk RAG.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="grade">Tingkat Kelas</Label>
              <Input
                id="grade"
                placeholder="Contoh: 10, 11, atau 12"
                value={gradeLevel}
                onChange={(e) => setGradeLevel(e.target.value)}
                disabled={isUploading}
              />
            </div>
            <div>
              <Label htmlFor="subject">Mata Pelajaran</Label>
              <Input
                id="subject"
                placeholder="Contoh: Biologi, Matematika"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                disabled={isUploading}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="pdf">File PDF Kurikulum</Label>
            <Input
              id="pdf"
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              disabled={isUploading}
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button type="submit" disabled={isUploading}>
            {isUploading ? "Mengunggah & Memproses..." : "Unggah Dokumen"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
