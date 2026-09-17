"use client";

import { useEffect, useState } from "react";
import { CurriculumDocument, getCurriculumDocuments } from "@/lib/api/curriculum";
import { UploadForm } from "@/components/features/curriculum/UploadForm";
import { CurriculumList } from "@/components/features/curriculum/CurriculumList";
import { useSession } from "next-auth/react";

export default function CurriculumPage() {
  const { data: session } = useSession();
  const [documents, setDocuments] = useState<CurriculumDocument[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

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
    fetchDocs();
  }, []);

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
