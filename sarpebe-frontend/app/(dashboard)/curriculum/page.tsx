"use client";

import { useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { useCurriculumDocuments } from "@/lib/hooks/useCurriculum";
import { UploadForm } from "@/components/features/curriculum/UploadForm";
import { CurriculumList } from "@/components/features/curriculum/CurriculumList";
import { Sheet } from "@/components/brand/Sheet";
import { buttonVariants } from "@/components/ui/button";
import { Notice } from "@/components/ui/notice";
import { Pagination } from "@/components/ui/pagination";

const PAGE_SIZE = 10;

export default function CurriculumPage() {
  const { data: session, status } = useSession();
  const role = session?.user.role;
  const isAdmin = status === "authenticated" && role === "admin";
  const [page, setPage] = useState(0);

  const { data, isLoading, isError } = useCurriculumDocuments(page * PAGE_SIZE, PAGE_SIZE, isAdmin);
  const documents = data?.items ?? [];
  const pageCount = Math.max(1, Math.ceil((data?.total ?? 0) / PAGE_SIZE));
  // Deleting the only document on the last page leaves an empty page; step back to the previous one.
  const pastTheEnd = !isLoading && !isError && documents.length === 0 && page > 0;

  if (status === "loading") {
    return <p className="py-16 text-center text-ink-soft" role="status">Memeriksa hak akses...</p>;
  }

  // Client-side fallback; the route is also guarded by middleware and the API.
  if (role !== "admin") {
    return (
      <div className="mx-auto max-w-xl">
        <Sheet margin className="py-10 pr-6 sm:pr-10">
          <h1 className="text-3xl font-bold">Khusus administrator</h1>
          <p className="mt-3 text-ink-soft">
            Dokumen kurikulum hanya bisa dikelola oleh akun administrator. Akun Anda terdaftar sebagai guru.
          </p>
          <Link href="/lesson-plans" className={buttonVariants({ className: "mt-6" })}>
            Kembali ke modul ajar
          </Link>
        </Sheet>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl lg:text-4xl">Dokumen kurikulum</h1>
        <p className="mt-2 max-w-2xl text-ink-soft">
          Dokumen yang diindeks di sini menjadi satu-satunya sumber modul ajar. Guru melihat rujukannya
          sebagai nama dokumen dan halaman.
        </p>
      </div>

      <UploadForm />

      <section aria-labelledby="daftar-dokumen" className="space-y-4">
        <h2 id="daftar-dokumen" className="text-2xl font-bold">
          Dokumen terunggah
        </h2>
        {isLoading ? (
          <p className="py-8 text-ink-soft" role="status">Memuat dokumen...</p>
        ) : isError ? (
          <Notice tone="error">
            <p>Daftar dokumen belum bisa dimuat. Muat ulang halaman, atau coba lagi nanti.</p>
          </Notice>
        ) : pastTheEnd ? (
          <Notice tone="info">
            <p>Halaman ini sudah kosong.</p>
            <button
              type="button"
              onClick={() => setPage(pageCount - 1)}
              className="font-semibold underline underline-offset-4 hover:no-underline"
            >
              Kembali ke halaman terakhir
            </button>
          </Notice>
        ) : (
          <>
            <CurriculumList documents={documents} />
            <Pagination page={page} pageCount={pageCount} onPageChange={setPage} label="Halaman daftar dokumen" />
          </>
        )}
      </section>
    </div>
  );
}
