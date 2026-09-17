"use client";

import { useEffect, useState } from "react";
import { CurriculumDocument, getCurriculumDocuments } from "@/lib/api/curriculum";
import { UploadForm } from "@/components/features/curriculum/UploadForm";
import { CurriculumList } from "@/components/features/curriculum/CurriculumList";
import { useSession } from "next-auth/react";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function CurriculumPage() {
  const { data: session, status } = useSession();
  const [documents, setDocuments] = useState<CurriculumDocument[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const role = (session?.user as any)?.role;

  const fetchDocs = async () => {
    try {
      setLoading(true);
      const data = await getCurriculumDocuments();
      setDocuments(data);
    } catch (err) {
      console.error("Gagal mengambil data kurikulum:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (status === "authenticated" && role === "admin") {
      fetchDocs();
    }
  }, [status, role]);

  if (status === "loading") {
    return (
      <div className="container mx-auto p-12 text-center text-slate-500">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3"></div>
        Memeriksa hak akses...
      </div>
    );
  }

  // Client-side guard fallback if accessed directly
  if (role !== "admin") {
    return (
      <div className="container mx-auto px-6 py-16 max-w-lg text-center">
        <div className="bg-white border border-rose-100 rounded-2xl p-8 shadow-xs">
          <div className="h-14 w-14 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-4">
            <ShieldAlert className="h-7 w-7" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 mb-2">Akses Ditolak (403)</h2>
          <p className="text-slate-600 text-sm mb-6 leading-relaxed">
            Halaman Manajemen Dokumen Kurikulum hanya dapat diakses oleh akun dengan peran <strong>Admin</strong>. Akun Anda saat ini memiliki peran sebagai <strong>Guru / Pengajar</strong>.
          </p>
          <Link href="/lesson-plans">
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Kembali ke Modul Ajar
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Manajemen Kurikulum</h1>
          <p className="text-gray-500 mt-1">
            Kelola dokumen kurikulum acuan RAG untuk menyelaraskan RPP secara otomatis.
          </p>
        </div>
      </div>

      <UploadForm onUploadSuccess={fetchDocs} />

      <h2 className="text-xl font-semibold mb-4 text-gray-800">Daftar Dokumen Kurikulum</h2>
      {loading ? (
        <div className="text-center p-8">Memuat dokumen...</div>
      ) : (
        <CurriculumList documents={documents} onDocumentDeleted={fetchDocs} />
      )}
    </div>
  );
}
