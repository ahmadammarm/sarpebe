"use client";

import { CurriculumDocument, deleteCurriculumDocument } from "@/lib/api/curriculum";
import { Button } from "@/components/ui/button";
import { Trash2, FileText, CheckCircle2, Clock, AlertCircle, ExternalLink } from "lucide-react";
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
      <div className="text-center p-12 bg-white border border-slate-200/80 rounded-xl shadow-xs">
        <div className="h-12 w-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
          <FileText className="h-6 w-6" />
        </div>
        <h3 className="font-semibold text-slate-800 mb-1">Belum Ada Dokumen Kurikulum</h3>
        <p className="text-slate-500 text-sm max-w-sm mx-auto">
          Unggah file PDF Capaian Pembelajaran untuk mulai mengaktifkan fitur pencarian RAG.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-slate-200/80 rounded-xl overflow-hidden bg-white shadow-xs">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 text-sm">
          <thead className="bg-slate-50 text-slate-500 font-semibold text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-3.5 text-left">Judul Dokumen</th>
              <th className="px-6 py-3.5 text-left">Tipe</th>
              <th className="px-6 py-3.5 text-left">Status Pemrosesan</th>
              <th className="px-6 py-3.5 text-left">Waktu Unggah</th>
              <th className="px-6 py-3.5 text-right">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-emerald-50/30 transition-colors">
                <td className="px-6 py-4 font-semibold text-slate-900">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                      <FileText className="h-4 w-4" />
                    </div>
                    <a
                      href={doc.url_path}
                      target="_blank"
                      rel="noreferrer"
                      className="hover:text-emerald-700 inline-flex items-center gap-1 group"
                    >
                      <span>{doc.title}</span>
                      <ExternalLink className="h-3 w-3 text-slate-400 group-hover:text-emerald-600" />
                    </a>
                  </div>
                </td>
                <td className="px-6 py-4 text-slate-500 uppercase text-xs font-semibold">{doc.document_type}</td>
                <td className="px-6 py-4">
                  {doc.status === "completed" && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                      <CheckCircle2 className="h-3 w-3" />
                      Terindeks
                    </span>
                  )}
                  {doc.status === "processing" && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                      <Clock className="h-3 w-3 animate-spin" />
                      Memproses Vektor
                    </span>
                  )}
                  {doc.status === "failed" && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
                      <AlertCircle className="h-3 w-3" />
                      Gagal
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-slate-500 text-xs">
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
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    className="text-slate-400 hover:text-rose-600 hover:bg-rose-50"
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
    </div>
  );
}
