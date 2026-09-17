"use client";

import { useState } from "react";
import { LessonPlan, updateLessonPlan, downloadLessonPlanPdf } from "@/lib/api/lesson-plans";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Download, Save, BookOpen, Target, Sparkles, FileText, CheckCircle2, Bookmark } from "lucide-react";

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
      {/* Action Header Card */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Kelas {plan.grade_level}
            </span>
            <span className="text-slate-400">•</span>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              {plan.subject}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-emerald-950 tracking-tight">
            {content.title || plan.topic}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            type="button"
            className="border-emerald-200 text-emerald-800 hover:bg-emerald-50"
            onClick={async () => {
              try {
                await downloadLessonPlanPdf(plan.id, content.title || plan.topic);
              } catch (e) {
                alert("Gagal mengunduh PDF modul ajar.");
              }
            }}
          >
            <Download className="h-4 w-4 mr-2 text-emerald-600" />
            Unduh PDF
          </Button>
          <Button onClick={handleSave} disabled={isSaving} className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-600/20">
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? "Menyimpan..." : "Simpan Perubahan"}
          </Button>
        </div>
      </div>

      {saveSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          Perubahan pada modul ajar berhasil disimpan ke basis data!
        </div>
      )}

      {/* 1. Informasi Umum */}
      <Card className="border-slate-200/80 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-50">
          <CardTitle className="text-base font-bold text-emerald-950 flex items-center gap-2">
            <FileText className="h-4 w-4 text-emerald-600" />
            1. Informasi Umum & Judul Modul
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <div>
            <Label className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1.5 block">
              Judul Modul Ajar
            </Label>
            <Input
              value={content.title || ""}
              onChange={(e) => updateField("title", e.target.value)}
              className="font-medium text-slate-900 focus-visible:ring-emerald-500"
            />
          </div>
        </CardContent>
      </Card>

      {/* 2. Tujuan Pembelajaran */}
      <Card className="border-slate-200/80 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-50">
          <CardTitle className="text-base font-bold text-emerald-950 flex items-center gap-2">
            <Target className="h-4 w-4 text-emerald-600" />
            2. Tujuan Pembelajaran (Capaian Pembelajaran)
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <textarea
            className="w-full min-h-[120px] p-3.5 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500 leading-relaxed font-sans"
            value={Array.isArray(content.objectives) ? content.objectives.join("\n") : content.objectives || ""}
            onChange={(e) => updateField("objectives", e.target.value.split("\n"))}
            placeholder="Pisahkan setiap tujuan dengan baris baru (enter)"
          />
        </CardContent>
      </Card>

      {/* 3. Media & Sumber Belajar */}
      <Card className="border-slate-200/80 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-50">
          <CardTitle className="text-base font-bold text-emerald-950 flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-emerald-600" />
            3. Media & Sumber Belajar
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <textarea
            className="w-full min-h-[100px] p-3.5 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500 leading-relaxed font-sans"
            value={Array.isArray(content.materials) ? content.materials.join("\n") : content.materials || ""}
            onChange={(e) => updateField("materials", e.target.value.split("\n"))}
            placeholder="Pisahkan materi/media dengan baris baru"
          />
        </CardContent>
      </Card>

      {/* 4. Penilaian / Asesmen */}
      <Card className="border-slate-200/80 shadow-xs">
        <CardHeader className="pb-3 border-b border-slate-50">
          <CardTitle className="text-base font-bold text-emerald-950 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-emerald-600" />
            4. Penilaian & Asesmen
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <textarea
            className="w-full min-h-[100px] p-3.5 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500 leading-relaxed font-sans"
            value={content.assessment || ""}
            onChange={(e) => updateField("assessment", e.target.value)}
          />
        </CardContent>
      </Card>

      {/* 5. Sitasi & Referensi Dokumen Kurikulum */}
      {content.citations && content.citations.length > 0 && (
        <Card className="border-emerald-200/70 bg-emerald-50/40 shadow-xs">
          <CardHeader className="pb-3 border-b border-emerald-100">
            <CardTitle className="text-base font-bold text-emerald-950 flex items-center gap-2">
              <Bookmark className="h-4 w-4 text-emerald-600" />
              5. Referensi & Sitasi Dokumen Resmi (Grounding RAG)
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <ul className="space-y-2 text-sm text-emerald-900">
              {content.citations.map((cite: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2 bg-white/80 p-2.5 rounded-lg border border-emerald-100">
                  <span className="h-5 w-5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span>{cite}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
