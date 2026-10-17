import Link from "next/link";
import { FaseTag } from "@/components/brand/FaseTag";
import { Mark } from "@/components/brand/Mark";
import { Sheet } from "@/components/brand/Sheet";
import { ThemeToggle } from "@/components/brand/ThemeToggle";
import { Wordmark } from "@/components/brand/Wordmark";
import { buttonVariants } from "@/components/ui/button";

const STEPS = [
  {
    title: "Pilih kelas, mata pelajaran, dan topik",
    body: "Tulis seperti biasa. Kelas 7 sampai 9 otomatis dikenali sebagai Fase D, kelas 10 sebagai Fase E.",
  },
  {
    title: "SARPEBE mencari bagian CP yang relevan",
    body: "Pencarian hanya memakai dokumen yang sudah diunggah administrator untuk kelas dan mata pelajaran itu. Jika dokumennya belum ada, Anda diberi tahu, bukan dikarang.",
  },
  {
    title: "Sunting, lalu unduh PDF",
    body: "Ubah tujuan, kegiatan, media, dan asesmen langsung di halaman. Sumber rujukan tetap tercantum di akhir modul.",
  },
];

const TRUST_POINTS = [
  {
    term: "Disusun dari dokumen Anda",
    detail: "Model diarahkan memakai hanya dokumen CP yang diunggah administrator, bukan sumber di luar itu.",
  },
  {
    term: "Halaman rujukan tercatat",
    detail: "Nama dokumen dan nomor halaman dicantumkan di setiap modul, sehingga bisa diperiksa satu per satu.",
  },
  {
    term: "Draf, bukan keputusan akhir",
    detail: "Tetap baca hasilnya sebelum dipakai mengajar. Anda yang menentukan versi akhirnya.",
  },
];

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-rule bg-paper">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-5 sm:px-8">
          <Link href="/" aria-label="SARPEBE, ke halaman depan" className="rounded-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/40">
            <Wordmark />
          </Link>
          <nav aria-label="Akun" className="flex items-center gap-1 sm:gap-2">
            <ThemeToggle />
            <Link href="/login" className={buttonVariants({ variant: "ghost" })}>
              Masuk
            </Link>
            <Link href="/register" className={buttonVariants()}>
              Buat akun
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero: the product's promise, next to what it produces. */}
        <section className="ruled-page border-b border-rule">
          <div className="mx-auto grid w-full max-w-6xl gap-12 px-5 py-14 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.95fr)] lg:items-center lg:py-20">
            <div>
              <p className="font-hand text-2xl text-ink-soft">untuk guru Kurikulum Merdeka</p>
              <h1 className="mt-2 text-4xl font-bold leading-[1.08] sm:text-5xl lg:text-6xl">
                Susun modul ajar dari <Mark>Capaian Pembelajaran</Mark> yang resmi.
              </h1>
              <p className="mt-6 max-w-xl text-lg text-ink-soft">
                Pilih kelas, mata pelajaran, dan topik. SARPEBE membaca dokumen CP yang diunggah administrator,
                menyusun draf modul ajar, lalu mencantumkan halaman rujukannya. Anda tinggal menyunting dan
                mengunduh PDF.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link href="/register" className={buttonVariants({ size: "lg" })}>
                  Buat akun
                </Link>
                <Link href="/login" className={buttonVariants({ size: "lg", variant: "outline" })}>
                  Sudah punya akun? Masuk
                </Link>
              </div>
            </div>

            <figure>
              <figcaption className="mb-2 font-hand text-xl text-ink-soft">Contoh hasil</figcaption>
              <Sheet margin className="py-6 pr-5 sm:pr-8">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-semibold">Kelas 9</span>
                  <FaseTag grade="9" />
                  <span className="text-ink-soft">IPS</span>
                </div>
                <h2 className="mt-2 text-2xl font-bold leading-tight">Pelaku dan kegiatan ekonomi</h2>

                <h3 className="mt-6 text-sm font-semibold uppercase tracking-wide text-ink-soft">Tujuan pembelajaran</h3>
                <p className="mt-2 leading-7">
                  Peserta didik mampu <Mark>menganalisis interaksi antarpelaku ekonomi</Mark> dalam kegiatan
                  produksi, distribusi, dan konsumsi.
                </p>
                <p className="mt-1 font-hand text-lg text-margin-text">kutipan dari CP, halaman 14</p>

                <h3 className="mt-6 text-sm font-semibold uppercase tracking-wide text-ink-soft">Sumber rujukan</h3>
                <p className="mt-2 text-sm">
                  <Mark>Dokumen CP IPS, hlm. 14</Mark>
                </p>
              </Sheet>
            </figure>
          </div>
        </section>

        {/* How it works: a real sequence, so the numbers carry information. */}
        <section aria-labelledby="cara-kerja" className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 lg:py-24">
          <h2 id="cara-kerja" className="max-w-2xl text-3xl font-bold sm:text-4xl">
            Tiga langkah, tanpa mulai dari halaman kosong.
          </h2>
          <ol className="mt-10 divide-y divide-rule border-y border-rule">
            {STEPS.map((step, index) => (
              <li key={step.title} className="grid gap-2 py-6 sm:grid-cols-[5rem_minmax(0,1fr)_minmax(0,1.3fr)] sm:items-baseline sm:gap-8">
                <span aria-hidden className="font-hand text-5xl leading-none text-ballpoint">{index + 1}</span>
                <h3 className="text-xl font-semibold">{step.title}</h3>
                <p className="text-ink-soft">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Why it can be reviewed. */}
        <section aria-labelledby="dapat-ditinjau" className="border-y border-rule bg-sheet">
          <div className="mx-auto grid w-full max-w-6xl gap-10 px-5 py-16 sm:px-8 lg:grid-cols-2 lg:py-24">
            <div>
              <h2 id="dapat-ditinjau" className="text-3xl font-bold sm:text-4xl">
                Setiap modul menyebut sumbernya.
              </h2>
              <p className="mt-5 max-w-lg text-lg text-ink-soft">
                Kepala sekolah atau pengawas bisa memeriksa dari mana sebuah tujuan pembelajaran berasal.
                Rujukan ditampilkan sebagai nama dokumen dan halaman, ditandai seperti stabilo di bagian
                Sumber rujukan.
              </p>
            </div>
            <dl className="divide-y divide-rule border-y border-rule">
              {TRUST_POINTS.map((point) => (
                <div key={point.term} className="py-5">
                  <dt className="text-lg font-semibold">{point.term}</dt>
                  <dd className="mt-1 text-ink-soft">{point.detail}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* Administrators. */}
        <section aria-labelledby="administrator" className="mx-auto w-full max-w-6xl px-5 py-16 sm:px-8 lg:py-24">
          <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-start">
            <div>
              <h2 id="administrator" className="text-3xl font-bold sm:text-4xl">
                Untuk administrator kurikulum
              </h2>
              <p className="mt-5 max-w-lg text-lg text-ink-soft">
                Dokumen yang Anda unggah menjadi satu-satunya sumber modul ajar. Karena itu, label kelas dan
                mata pelajarannya perlu tepat.
              </p>
              <Link href="/login" className={buttonVariants({ variant: "outline", className: "mt-6" })}>
                Masuk sebagai administrator
              </Link>
            </div>
            <ul className="space-y-4 text-lg">
              <li className="flex gap-3">
                <span aria-hidden className="mt-3 size-1.5 shrink-0 rounded-full bg-margin" />
                Unggah PDF Capaian Pembelajaran, Alur Tujuan Pembelajaran, atau Buku Guru.
              </li>
              <li className="flex gap-3">
                <span aria-hidden className="mt-3 size-1.5 shrink-0 rounded-full bg-margin" />
                Tentukan kelas dan mata pelajaran yang dicakup setiap dokumen.
              </li>
              <li className="flex gap-3">
                <span aria-hidden className="mt-3 size-1.5 shrink-0 rounded-full bg-margin" />
                Pantau pengindeksan: memproses, terindeks, atau gagal.
              </li>
            </ul>
          </div>
        </section>

        <section className="border-t border-rule bg-sheet">
          <div className="mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-5 py-14 sm:px-8 md:flex-row md:items-center md:justify-between">
            <p className="max-w-xl text-2xl font-bold leading-snug sm:text-3xl">Mulai dari satu topik yang akan Anda ajarkan minggu ini.</p>
            <Link href="/register" className={buttonVariants({ size: "lg" })}>
              Buat akun
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-rule bg-paper">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-5 py-8 text-sm text-ink-soft sm:px-8 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <Wordmark className="text-base" />
            <span>Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum</span>
          </div>
          <nav aria-label="Tautan kaki" className="flex gap-5">
            <Link href="/login" className="underline-offset-4 hover:underline">Masuk</Link>
            <Link href="/register" className="underline-offset-4 hover:underline">Buat akun</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
