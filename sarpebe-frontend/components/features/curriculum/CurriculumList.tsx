"use client";

import { CurriculumDocument, deleteCurriculumDocument } from "@/lib/api/curriculum";
import { Button } from "@/components/ui/button";
import { Trash2, FileText, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { useState } from "react";

interface CurriculumListProps {
  documents: CurriculumDocument[];
  onDocumentDeleted: () => void;
}

export function CurriculumList({ documents, onDocumentDeleted }: CurriculumListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    if (!confirm("Apakah Anda yakin ingin menghapus dokumen kurikulum ini beserta data vektornya?")) {
      return;
    }

    try {
      setDeletingId(id);
      await deleteCurriculumDocument(id);
      onDocumentDeleted();
    } catch (err) {
      alert("Gagal menghapus dokumen kurikulum.");
    } finally {
      setDeletingId(null);
    }
  };

  if (documents.length === 0) {
    return (
      <div className="text-center p-8 bg-gray-50 border rounded-lg">
        <FileText className="mx-auto h-12 w-12 text-gray-400 mb-2" />
        <p className="text-gray-600">Belum ada dokumen kurikulum yang diunggah.</p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg overflow-hidden bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Judul File</th>
            <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Tipe</th>
            <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Status</th>
            <th className="px-6 py-3 text-left font-medium text-gray-500 uppercase">Waktu Unggah</th>
            <th className="px-6 py-3 text-right font-medium text-gray-500 uppercase">Aksi</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td className="px-6 py-4 font-medium text-gray-900 flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-500" />
                <a href={doc.url_path} target="_blank" rel="noreferrer" className="hover:underline">
                  {doc.title}
                </a>
              </td>
              <td className="px-6 py-4 text-gray-500 uppercase">{doc.document_type}</td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  {doc.status === "completed" && <CheckCircle className="h-3.5 w-3.5 text-green-500" />}
                  {doc.status === "processing" && <Clock className="h-3.5 w-3.5 text-amber-500 animate-spin" />}
                  {doc.status === "failed" && <AlertCircle className="h-3.5 w-3.5 text-red-500" />}
                  {doc.status}
                </span>
              </td>
              <td className="px-6 py-4 text-gray-500">
                {new Date(doc.uploaded_at).toLocaleDateString("id-ID", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </td>
              <td className="px-6 py-4 text-right">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(doc.id)}
                  disabled={deletingId === doc.id}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  {deletingId === doc.id ? "Menghapus..." : "Hapus"}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
