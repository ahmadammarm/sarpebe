import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Sparkles, BookOpen, ShieldCheck, FileCheck, ArrowRight, CheckCircle2 } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#F8FAF9] text-foreground flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <span className="font-extrabold text-xl tracking-tight text-emerald-950">SARPEBE</span>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-emerald-800 hover:text-emerald-900 hover:bg-emerald-50">
                Masuk
              </Button>
            </Link>
            <Link href="/register">
              <Button className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-600/20">
                Daftar Akun
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 md:py-28 px-6 flex-1 flex flex-col items-center justify-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-100/70 border border-emerald-200 text-emerald-800 text-xs font-semibold mb-6 animate-fade-in">
          <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
          Didukung AI Gemini & Retrieval-Augmented Generation (RAG)
        </div>

        <h1 className="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-emerald-950 leading-[1.15]">
          Penyusunan Modul Ajar & RPP Berstandar Kurikulum Merdeka
        </h1>

        <p className="mt-6 max-w-2xl text-lg sm:text-xl text-slate-600 leading-relaxed">
          SARPEBE membantu pendidik Indonesia menyusun modul ajar komprehensif, akurat, dan grounded secara otomatis mengacu pada Capaian Pembelajaran (CP) dan Alur Tujuan Pembelajaran resmi.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row gap-3 sm:gap-4 w-full justify-center max-w-md">
          <Link href="/lesson-plans" className="w-full sm:w-auto">
            <Button size="lg" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-base h-12 px-6 shadow-md shadow-emerald-600/25">
              Buka Dashboard
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
          <Link href="/login" className="w-full sm:w-auto">
            <Button size="lg" variant="outline" className="w-full border-slate-200 hover:bg-emerald-50 hover:text-emerald-900 text-slate-700 font-medium text-base h-12 px-6">
              Masuk Guru
            </Button>
          </Link>
        </div>

        {/* Feature Highlights Grid */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl text-left">
          <div className="p-6 rounded-xl bg-white border border-emerald-100 shadow-sm hover:border-emerald-300 transition-colors">
            <div className="h-10 w-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-lg text-emerald-950 mb-2">Terverifikasi Sesuai CP/ATP</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Modul ajar disusun berbasis dokumen kurikulum resmi kementerian, meminimalisir halusinasi AI berkat semantic vector search.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-white border border-emerald-100 shadow-sm hover:border-emerald-300 transition-colors">
            <div className="h-10 w-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <BookOpen className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-lg text-emerald-950 mb-2">Sitasi Halaman Resmi</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Setiap tujuan dan materi dilengkapi rujukan halaman dokumen asli agar mudah ditinjau oleh pengawas sekolah dan kepala sekolah.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-white border border-emerald-100 shadow-sm hover:border-emerald-300 transition-colors">
            <div className="h-10 w-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <FileCheck className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-lg text-emerald-950 mb-2">Ekspor & Edit Fleksibel</h3>
            <p className="text-slate-600 text-sm leading-relaxed">
              Kustomisasi isi rencana pembelajaran langsung di browser dan unduh dokumen siap cetak dalam format PDF rapi.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white py-8 px-6 text-center text-sm text-slate-500">
        <p>© {new Date().getFullYear()} SARPEBE — Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum.</p>
      </footer>
    </div>
  );
}
