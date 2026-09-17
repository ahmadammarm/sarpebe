"use client";

import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useEffect, useState } from "react";
import { LessonPlan, getLessonPlans, deleteLessonPlan, downloadLessonPlanPdf } from "@/lib/api/lesson-plans";
import { Plus, Trash2, Download, Edit3, BookOpen, Sparkles, Clock, CheckCircle2, AlertCircle } from "lucide-react";

export function LessonPlanDashboard() {
  const { data: session, status } = useSession();
  const [plans, setPlans] = useState<LessonPlan[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const data = await getLessonPlans();
      setPlans(data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (status === "authenticated") {
      fetchPlans();
    }
  }, [status]);

  const handleDelete = async (id: string) => {
    if (!confirm("Hapus modul ajar ini?")) return;
    try {
      await deleteLessonPlan(id);
      fetchPlans();
    } catch (err) {
      alert("Gagal menghapus rencana pembelajaran.");
    }
  };

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center p-20 text-slate-500">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mr-3"></div>
        Memuat sesi akun...
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="container mx-auto p-12 text-center max-w-md">
        <div className="p-8 bg-white border border-emerald-100 rounded-2xl shadow-sm">
          <AlertCircle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-800 mb-2">Akses Terbatas</h2>
          <p className="text-slate-500 text-sm mb-6">Silakan masuk ke akun SARPEBE Anda terlebih dahulu.</p>
          <Link href="/login">
            <Button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white">Menuju Halaman Masuk</Button>
          </Link>
        </div>
      </div>
    );
  }

  const completedCount = plans.filter((p) => p.status === "completed").length;
  const pendingCount = plans.filter((p) => p.status === "pending" || p.status === "processing").length;

  return (
    <div className="container mx-auto px-6 py-8 max-w-6xl">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-emerald-950 tracking-tight">Rencana Pembelajaran (Modul Ajar)</h1>
          <p className="text-slate-600 text-sm mt-1">
            Susun dan kelola modul ajar Kurikulum Merdeka yang diground ke dokumen Capaian Pembelajaran resmi.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/lesson-plans/new">
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-600/20">
              <Plus className="h-4 w-4 mr-2" />
              Buat Modul Ajar Baru
            </Button>
          </Link>
          {(session?.user as any)?.role === "admin" && (
            <Link href="/curriculum">
              <Button variant="outline" className="border-emerald-200 text-emerald-800 hover:bg-emerald-50">
                <BookOpen className="h-4 w-4 mr-2" />
                Dokumen Kurikulum
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-white border border-emerald-100 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Modul Ajar</span>
            <Sparkles className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-950 mt-2">{plans.length}</div>
        </div>

        <div className="bg-white border border-emerald-100 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Selesai Disusun</span>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </div>
          <div className="text-2xl font-extrabold text-green-700 mt-2">{completedCount}</div>
        </div>

        <div className="bg-white border border-emerald-100 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sedang Diproses</span>
            <Clock className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-2xl font-extrabold text-amber-600 mt-2">{pendingCount}</div>
        </div>
      </div>

      {/* Lesson Plans Table Card */}
      <div className="bg-white border border-slate-200/80 rounded-xl overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <h2 className="font-bold text-slate-800 text-sm">Daftar Modul Ajar Tersimpan</h2>
          <span className="text-xs text-slate-500">{plans.length} Dokumen</span>
        </div>

        {loading ? (
          <div className="p-16 text-center text-slate-400 text-sm flex flex-col items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mb-3"></div>
            Memuat daftar modul ajar...
          </div>
        ) : plans.length === 0 ? (
          <div className="p-16 text-center text-slate-500">
            <div className="h-12 w-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-slate-800 mb-1">Belum Ada Modul Ajar</h3>
            <p className="text-sm text-slate-500 max-w-sm mx-auto mb-5">
              Mulai buat modul ajar otomatis pertama Anda berbasis Capaian Pembelajaran (CP).
            </p>
            <Link href="/lesson-plans/new">
              <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">
                <Plus className="h-4 w-4 mr-2" />
                Buat Modul Ajar Sekarang
              </Button>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50 text-slate-500 font-semibold text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3 text-left">Topik / Materi</th>
                  <th className="px-6 py-3 text-left">Mata Pelajaran</th>
                  <th className="px-6 py-3 text-left">Tingkat Kelas</th>
                  <th className="px-6 py-3 text-left">Status</th>
                  <th className="px-6 py-3 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {plans.map((plan) => (
                  <tr key={plan.id} className="hover:bg-emerald-50/30 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      <Link href={`/lesson-plans/${plan.id}`} className="hover:text-emerald-700 transition-colors">
                        {plan.topic}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-slate-600">{plan.subject}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200/60">
                        Kelas {plan.grade_level}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {plan.status === "completed" && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                          <CheckCircle2 className="h-3 w-3" />
                          Siap
                        </span>
                      )}
                      {(plan.status === "pending" || plan.status === "processing") && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                          <Clock className="h-3 w-3 animate-spin" />
                          Diproses
                        </span>
                      )}
                      {plan.status === "failed" && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
                          <AlertCircle className="h-3 w-3" />
                          Gagal
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2 whitespace-nowrap">
                      <Link href={`/lesson-plans/${plan.id}`}>
                        <Button variant="outline" size="sm" className="border-slate-200 hover:bg-emerald-50 hover:text-emerald-800">
                          <Edit3 className="h-3.5 w-3.5 mr-1" />
                          Edit
                        </Button>
                      </Link>
                      {plan.status === "completed" && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                          onClick={async () => {
                            try {
                              await downloadLessonPlanPdf(plan.id, plan.topic);
                            } catch (e) {
                              alert("Gagal mengunduh PDF modul ajar.");
                            }
                          }}
                        >
                          <Download className="h-3.5 w-3.5 mr-1" />
                          PDF
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(plan.id)}
                        className="text-slate-400 hover:text-rose-600 hover:bg-rose-50"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
