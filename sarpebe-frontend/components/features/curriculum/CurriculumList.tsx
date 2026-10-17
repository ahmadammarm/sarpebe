"use client";

import { useState } from "react";
import { ExternalLink, Trash2 } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Sheet } from "@/components/brand/Sheet";
import { StatusStamp } from "@/components/brand/StatusStamp";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { useDeleteCurriculumDocument } from "@/lib/hooks/useCurriculum";
import { getErrorMessage } from "@/lib/utils/errors";
import type { CurriculumDocument } from "@/types/curriculum";

interface CurriculumListProps {
  documents: CurriculumDocument[];
}

const DOCUMENT_TYPE_LABELS: Record<CurriculumDocument["document_type"], string> = {
  CP: "Capaian Pembelajaran",
  ATP: "Alur Tujuan Pembelajaran",
  BUKU_GURU: "Buku Guru",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}

export function CurriculumList({ documents }: CurriculumListProps) {
  const deleteDocument = useDeleteCurriculumDocument();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = async (doc: CurriculumDocument) => {
    if (!confirm(`Hapus "${doc.title}" beserta seluruh isi yang sudah diindeks? Modul ajar tidak lagi bisa merujuk dokumen ini.`)) {
      return;
    }

    try {
      setDeletingId(doc.id);
      setDeleteError(null);
      await deleteDocument.mutateAsync(doc.id);
    } catch (err) {
      setDeleteError(getErrorMessage(err, "Dokumen belum bisa dihapus. Coba lagi."));
    } finally {
      setDeletingId(null);
    }
  };

  if (documents.length === 0) {
    return (
      <Sheet margin className="py-10 pr-6 sm:pr-10">
        <p className="font-hand text-3xl text-ink-soft">Belum ada dokumen.</p>
        <p className="mt-2 max-w-md text-ink-soft">
          Unggah PDF Capaian Pembelajaran lebih dulu. Tanpa dokumen, guru tidak bisa menyusun modul ajar.
        </p>
      </Sheet>
    );
  }

  return (
    <Sheet className="px-5 sm:px-8">
      {deleteError && (
        <Notice tone="error" className="mt-5">
          <p>{deleteError}</p>
        </Notice>
      )}
      <ul className="divide-y divide-rule">
        {documents.map((doc) => {
          const labelled = doc.grade_level || doc.subject;
          return (
            <li key={doc.id} className="grid gap-3 py-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:gap-6">
              <div className="min-w-0">
                <a
                  href={doc.url_path}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex max-w-full items-center gap-1.5 rounded-sm font-display text-lg font-semibold leading-snug underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring/40"
                >
                  <span className="truncate">{doc.title}</span>
                  <ExternalLink className="size-3.5 shrink-0 text-ink-soft" aria-hidden />
                  <span className="sr-only">(buka PDF di tab baru)</span>
                </a>
                <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-soft">
                  <span>{DOCUMENT_TYPE_LABELS[doc.document_type] ?? doc.document_type}</span>
                  <span aria-hidden>·</span>
                  {labelled ? (
                    <>
                      <span className="capitalize">Kelas {doc.grade_level ?? "-"}</span>
                      {doc.grade_level && <FaseTag grade={doc.grade_level} />}
                      <span aria-hidden>·</span>
                      <span className="capitalize">{doc.subject ?? "-"}</span>
                    </>
                  ) : (
                    <span className="font-medium text-margin-text">Tanpa label kelas dan mata pelajaran</span>
                  )}
                  <span aria-hidden>·</span>
                  <time dateTime={doc.uploaded_at}>{formatDate(doc.uploaded_at)}</time>
                </p>
              </div>

              <div className="flex items-center gap-2">
                <StatusStamp kind="document" status={doc.status} />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(doc)}
                  disabled={deletingId === doc.id}
                  aria-label={`Hapus dokumen ${doc.title}`}
                  className="text-ink-soft hover:bg-margin-wash hover:text-margin-text"
                >
                  <Trash2 aria-hidden />
                  {deletingId === doc.id ? "Menghapus..." : "Hapus"}
                </Button>
              </div>
            </li>
          );
        })}
      </ul>
    </Sheet>
  );
}
