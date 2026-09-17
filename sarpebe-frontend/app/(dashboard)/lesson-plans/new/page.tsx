"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createLessonPlan } from "@/lib/api/lesson-plans";
import { useJobSSE } from "@/lib/hooks/useJobSSE";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Sparkles, Loader2, CheckCircle2, AlertCircle, BookOpen, Layers, Compass } from "lucide-react";

export default function NewLessonPlanPage() {
  const router = useRouter();

  const [gradeLevel, setGradeLevel] = useState("");
  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [createdPlanId, setCreatedPlanId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { status: sseStatus, isDone, error: sseError } = useJobSSE(activeJobId);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gradeLevel || !subject || !topic) {
      setErrorMsg("Mohon lengkapi semua data formulir.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg(null);

      const response = await createLessonPlan({
        grade_level: gradeLevel,
        subject,
        topic,
      });

      setCreatedPlanId(response.id);
      setActiveJobId(response.job_id);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || "Gagal memulai pembuatan rencana pembelajaran.");
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    if (isDone && sseStatus === "completed" && createdPlanId) {
      const timer = setTimeout(() => {
        router.push(`/lesson-plans/${createdPlanId}`);
      }, 1200);
      return () => clearTimeout(timer);
    }
  }, [isDone, sseStatus, createdPlanId, router]);

  return (
    <div className="container mx-auto px-6 py-8 max-w-2xl">
      <Button
        variant="ghost"
        className="mb-6 text-slate-600 hover:text-emerald-800 hover:bg-emerald-50"
        onClick={() => router.push("/lesson-plans")}
        disabled={isSubmitting}
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Kembali ke Beranda
      </Button>

      <Card className="border-slate-200/80 shadow-xs overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-600 to-teal-700 p-6 text-white">
          <div className="flex items-center gap-2 text-emerald-100 text-xs font-semibold uppercase tracking-wider mb-2">
            <Sparkles className="h-4 w-4" />
            Generator AI Modul Ajar
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">Buat Modul Ajar Baru</h1>
          <p className="text-emerald-50 text-sm mt-1 leading-relaxed">
            AI Gemini akan menyusun modul pembelajaran terstruktur yang secara otomatis diselaraskan dengan dokumen Capaian Pembelajaran resmi.
          </p>
        </div>

        <CardContent className="p-6 sm:p-8">
          {!activeJobId ? (
            <form onSubmit={handleGenerate} className="space-y-5">
              <div className="space-y-1.5">
                <Label htmlFor="gradeLevel" className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="h-3.5 w-3.5 text-emerald-600" />
                  Tingkat Kelas
                </Label>
                <Input
                  id="gradeLevel"
                  placeholder="Misal: 10, 11, atau 12 (Fase E / F)"
                  value={gradeLevel}
                  onChange={(e) => setGradeLevel(e.target.value)}
                  disabled={isSubmitting}
                  className="focus-visible:ring-emerald-500"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="subject" className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <BookOpen className="h-3.5 w-3.5 text-emerald-600" />
                  Mata Pelajaran
                </Label>
                <Input
                  id="subject"
                  placeholder="Misal: Biologi, Matematika, Informatika"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  disabled={isSubmitting}
                  className="focus-visible:ring-emerald-500"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="topic" className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Compass className="h-3.5 w-3.5 text-emerald-600" />
                  Topik / Materi Pokok Pembelajaran
                </Label>
                <Input
                  id="topic"
                  placeholder="Misal: Struktur Sel Hewan dan Tumbuhan"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  disabled={isSubmitting}
                  className="focus-visible:ring-emerald-500"
                  required
                />
              </div>

              {errorMsg && (
                <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-sm rounded-xl flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
                  {errorMsg}
                </div>
              )}

              <div className="pt-2">
                <Button
                  type="submit"
                  size="lg"
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-600/25 h-11"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Memulai Pembuatan...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Susun Modul Ajar Otomatis
                    </>
                  )}
                </Button>
              </div>
            </form>
          ) : (
            <div className="py-10 text-center space-y-5">
              {sseStatus === "completed" ? (
                <>
                  <div className="h-16 w-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-sm animate-bounce">
                    <CheckCircle2 className="h-9 w-9" />
                  </div>
                  <h3 className="text-xl font-bold text-emerald-950">Penyusunan Selesai!</h3>
                  <p className="text-sm text-slate-600 max-w-sm mx-auto">
                    Modul ajar telah selesai digenerate dan diverifikasi. Mengalihkan ke editor modul...
                  </p>
                </>
              ) : sseStatus === "failed" || sseError ? (
                <>
                  <div className="h-16 w-16 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto shadow-sm">
                    <AlertCircle className="h-8 w-8" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900">Gagal Menyusun Modul</h3>
                  <p className="text-sm text-slate-600 max-w-sm mx-auto">
                    {sseError || "Terjadi kendala saat menghubungkan ke AI atau mengekstrak rujukan kurikulum."}
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setActiveJobId(null);
                      setIsSubmitting(false);
                    }}
                    className="mt-2"
                  >
                    Ulangi Proses
                  </Button>
                </>
              ) : (
                <>
                  <div className="relative flex items-center justify-center w-20 h-20 mx-auto">
                    <div className="absolute inset-0 rounded-full border-4 border-emerald-100 animate-ping opacity-75"></div>
                    <div className="h-16 w-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shadow-xs">
                      <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-emerald-950">
                      AI Sedang Menyusun Rencana Pembelajaran...
                    </h3>
                    <div className="inline-flex items-center gap-2 mt-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-800 text-xs font-semibold">
                      Status Pekerjaan: <span className="uppercase">{sseStatus}</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                    Sistem sedang mencari potongan teks Capaian Pembelajaran (CP) terkait di pgvector dan menyusun RPP berstandar Kemendikbud via Google Gemini.
                  </p>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
