"use client";

import { useState } from "react";
import { ExternalLink, Pencil, RefreshCw, Trash2 } from "lucide-react";
import { FaseTag } from "@/components/brand/FaseTag";
import { Sheet } from "@/components/brand/Sheet";
import { StatusStamp } from "@/components/brand/StatusStamp";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { DocumentEditForm } from "@/components/features/curriculum/DocumentEditForm";
import { useDeleteCurriculumDocument, useReindexCurriculumDocument } from "@/lib/hooks/useCurriculum";
import { DOCUMENT_TYPE_LABELS } from "@/lib/utils/curriculum";
import { getErrorMessage } from "@/lib/utils/errors";
import { formatDate } from "@/lib/utils/formatters";
import type { CurriculumDocument } from "@/types/curriculum";

interface CurriculumListProps {
  documents: CurriculumDocument[];
}

/** What the reading of the PDF found: the reason when it failed, otherwise notes worth a look. */
function IngestNotes({ doc }: { doc: CurriculumDocument }) {
  const notes = doc.ingest_warnings ?? [];
  if (notes.length === 0 || doc.status === "processing") return null;

  if (doc.status === "failed") {
    return <p className="mt-2 text-sm font-medium text-margin-text">{notes.join(" ")}</p>;
  }

  return (
    <details className="mt-2 text-sm text-ink-soft">
      <summary className="cursor-pointer rounded-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
        {notes.length} catatan pembacaan
      </summary>
      <ul className="mt-1.5 list-disc space-y-1 pl-5">
        {notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </details>
  );
}

export function CurriculumList({ documents }: CurriculumListProps) {
  const deleteDocument = useDeleteCurriculumDocument();
  const reindexDocument = useReindexCurriculumDocument();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleDelete = async (doc: CurriculumDocument) => {
    if (!confirm(`Hapus "${doc.title}" beserta seluruh isi yang sudah diindeks? Modul ajar tidak lagi bisa merujuk dokumen ini.`)) {
      return;
    }

    try {
      setBusyId(doc.id);
      setActionError(null);
      await deleteDocument.mutateAsync(doc.id);
    } catch (err) {
      setActionError(getErrorMessage(err, "Dokumen belum bisa dihapus. Coba lagi."));
    } finally {
      setBusyId(null);
    }
  };

  const handleReindex = async (doc: CurriculumDocument) => {
    if (!confirm(`Baca ulang "${doc.title}"? Isi yang diindeks diganti dengan hasil pembacaan baru, dan ini memakai layanan model.`)) {
      return;
    }

    try {
      setBusyId(doc.id);
      setActionError(null);
      await reindexDocument.mutateAsync(doc.id);
    } catch (err) {
      setActionError(getErrorMessage(err, "Dokumen belum bisa diproses ulang. Coba lagi."));
    } finally {
      setBusyId(null);
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
    <Sheet className="px-5 sm:px-6 lg:px-8">
      {actionError && (
        <Notice tone="error" className="mt-5">
          <p>{actionError}</p>
        </Notice>
      )}
      <ul className="divide-y divide-rule">
        {documents.map((doc, index) => {
          const labelled = doc.grade_level || doc.subject;
          const isProcessing = doc.status === "processing";
          const isBusy = busyId === doc.id;
          return (
            <li
              key={doc.id}
              className="row-in py-5"
              style={{ "--delay": `${Math.min(index, 8) * 45}ms` } as React.CSSProperties}
            >
              <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:gap-6">
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
                  <IngestNotes doc={doc} />
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <StatusStamp kind="document" status={doc.status} />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setEditingId(editingId === doc.id ? null : doc.id)}
                    disabled={isProcessing || isBusy}
                    aria-expanded={editingId === doc.id}
                    aria-label={`Edit dokumen ${doc.title}`}
                  >
                    <Pencil aria-hidden />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleReindex(doc)}
                    disabled={isProcessing || isBusy}
                    aria-label={`Proses ulang dokumen ${doc.title}`}
                  >
                    <RefreshCw aria-hidden />
                    Proses ulang
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(doc)}
                    disabled={isBusy}
                    aria-label={`Hapus dokumen ${doc.title}`}
                    className="text-ink-soft hover:bg-margin-wash hover:text-margin-text"
                  >
                    <Trash2 aria-hidden />
                    {isBusy && deleteDocument.isPending ? "Menghapus..." : "Hapus"}
                  </Button>
                </div>
              </div>

              {editingId === doc.id && (
                <div className="mt-4">
                  <DocumentEditForm document={doc} onDone={() => setEditingId(null)} />
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </Sheet>
  );
}
