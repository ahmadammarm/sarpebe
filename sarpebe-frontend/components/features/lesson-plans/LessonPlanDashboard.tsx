"use client";

import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useEffect, useState } from "react";
import { LessonPlan, getLessonPlans, deleteLessonPlan, getLessonPlanPdfExportUrl } from "@/lib/api/lesson-plans";
import { FileText, Plus, Trash2, Download, Edit3, BookOpen } from "lucide-react";

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
    return <div className="p-8">Loading session...</div>;
  }

  if (status === "unauthenticated") {
    return <div className="p-8">Access Denied. Please log in.</div>;
  }

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Rencana Pembelajaran (Modul Ajar)</h1>
          <p className="text-gray-600 mt-1">
            Selamat datang, <strong>{session?.user?.name || session?.user?.email}</strong>
          </p>
        </div>
        <div className="flex gap-3">
          <Link href="/curriculum">
            <Button variant="outline">
              <BookOpen className="h-4 w-4 mr-2" />
              Kelola Kurikulum
            </Button>
          </Link>
          <Button onClick={() => signOut({ callbackUrl: "/login" })} variant="destructive">
            Keluar
          </Button>
        </div>
      </div>

      <div className="bg-white border rounded-lg overflow-hidden shadow-sm">
        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
          <h2 className="font-semibold text-gray-800">Daftar Modul Ajar</h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">Memuat modul ajar...</div>
        ) : plans.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Belum ada modul ajar yang dibuat.</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Topik / Materi</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Mata Pelajaran</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Kelas</th>
                <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right font-medium text-gray-500 uppercase">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {plans.map((plan) => (
                <tr key={plan.id}>
                  <td className="px-6 py-4 font-medium text-gray-900">
                    <Link href={`/lesson-plans/${plan.id}`} className="text-blue-600 hover:underline">
                      {plan.topic}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-gray-500">{plan.subject}</td>
                  <td className="px-6 py-4 text-gray-500">Kelas {plan.grade_level}</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100">
                      {plan.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <Link href={`/lesson-plans/${plan.id}`}>
                      <Button variant="outline" size="sm">
                        <Edit3 className="h-4 w-4 mr-1" />
                        Edit
                      </Button>
                    </Link>
                    {plan.status === "completed" && (
                      <a href={getLessonPlanPdfExportUrl(plan.id)} target="_blank" rel="noreferrer">
                        <Button variant="outline" size="sm">
                          <Download className="h-4 w-4 mr-1" />
                          PDF
                        </Button>
                      </a>
                    )}
                    <Button variant="destructive" size="sm" onClick={() => handleDelete(plan.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
