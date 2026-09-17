"use client";

import { useState } from "react";
import { LessonPlan, updateLessonPlan, getLessonPlanPdfExportUrl } from "@/lib/api/lesson-plans";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Download, Save } from "lucide-react";

interface LessonPlanEditorProps {
  plan: LessonPlan;
  onUpdate: (updatedPlan: LessonPlan) => void;
}

export function LessonPlanEditor({ plan, onUpdate }: LessonPlanEditorProps) {
  const [content, setContent] = useState<any>(plan.generated_content || {});
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setSaveSuccess(false);
      const updated = await updateLessonPlan(plan.id, content);
      onUpdate(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert("Gagal menyimpan perubahan modul ajar.");
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = (field: string, value: any) => {
    setContent((prev: any) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">{content.title || plan.topic}</h2>
          <p className="text-gray-500">Kelas {plan.grade_level} • {plan.subject}</p>
        </div>
        <div className="flex gap-2">
          <a
            href={getLessonPlanPdfExportUrl(plan.id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex"
          >
            <Button variant="outline" type="button">
              <Download className="h-4 w-4 mr-2" />
              Unduh PDF
            </Button>
          </a>
          <Button onClick={handleSave} disabled={isSaving}>
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? "Menyimpan..." : "Simpan Perubahan"}
          </Button>
        </div>
      </div>

      {saveSuccess && (
        <div className="p-3 bg-green-50 border border-green-200 text-green-700 rounded-md text-sm">
          Perubahan berhasil disimpan!
        </div>
      )}

      {/* Form sections */}
      <Card>
        <CardHeader>
          <CardTitle>1. Judul & Informasi Umum</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Judul Modul</Label>
            <Input
              value={content.title || ""}
              onChange={(e) => updateField("title", e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>2. Tujuan Pembelajaran</CardTitle>
        </CardHeader>
        <CardContent>
          <textarea
            className="w-full min-h-[120px] p-3 border rounded-md text-sm"
            value={Array.isArray(content.objectives) ? content.objectives.join("\n") : content.objectives || ""}
            onChange={(e) => updateField("objectives", e.target.value.split("\n"))}
            placeholder="Pisahkan setiap tujuan dengan baris baru"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>3. Media & Sumber Belajar</CardTitle>
        </CardHeader>
        <CardContent>
          <textarea
            className="w-full min-h-[100px] p-3 border rounded-md text-sm"
            value={Array.isArray(content.materials) ? content.materials.join("\n") : content.materials || ""}
            onChange={(e) => updateField("materials", e.target.value.split("\n"))}
            placeholder="Pisahkan materi dengan baris baru"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>4. Penilaian / Asesmen</CardTitle>
        </CardHeader>
        <CardContent>
          <textarea
            className="w-full min-h-[100px] p-3 border rounded-md text-sm"
            value={content.assessment || ""}
            onChange={(e) => updateField("assessment", e.target.value)}
          />
        </CardContent>
      </Card>

      {content.citations && (
        <Card>
          <CardHeader>
            <CardTitle>5. Referensi & Sitasi Dokumen Kurikulum</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {content.citations.map((cite: string, idx: number) => (
                <li key={idx}>{cite}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
