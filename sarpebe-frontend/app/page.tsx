import Link from "next/link";
import { FaseTag } from "@/components/brand/FaseTag";
import { Mark } from "@/components/brand/Mark";
import { Reveal } from "@/components/brand/Reveal";
import { Sheet } from "@/components/brand/Sheet";
import { Wordmark } from "@/components/brand/Wordmark";
import { buttonVariants } from "@/components/ui/button";
import { FaqList } from "@/components/landing/FaqList";
import { FaseFinder } from "@/components/landing/FaseFinder";
import { LandingHeader } from "@/components/landing/LandingHeader";
import { LANDING_MENU } from "@/components/landing/menu";
import { SampleModule } from "@/components/landing/SampleModule";

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
    body: "Ubah tujuan, tabel kegiatan, rubrik, dan lampiran langsung di halaman. Sumber rujukan tetap tercantum di akhir modul.",
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

const ADMIN_POINTS = [
  "Unggah PDF Capaian Pembelajaran, Alur Tujuan Pembelajaran, atau Buku Guru.",
  "Tentukan kelas dan mata pelajaran yang dicakup setiap dokumen.",
  "Pantau pengindeksan: memproses, terindeks, atau gagal.",
];

/** Staggers an element's entrance on page load (see .rise in globals.css). */
function delay(ms: number): React.CSSProperties {
  return { "--delay": `${ms}ms` } as React.CSSProperties;
}

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <LandingHeader />

      <main className="flex-1">
        {/* Hero: the product's promise, next to what it produces. Enters in sequence on load. */}
        <section id="beranda" className="ruled-page border-b border-rule">
          <div className="mx-auto grid w-full max-w-6xl gap-10 px-5 py-10 sm:px-6 sm:py-14 lg:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.95fr)] lg:items-center lg:gap-12 lg:py-20">
            <div>
              <p className="rise font-hand text-xl text-ink-soft sm:text-2xl" style={delay(0)}>
                untuk guru Kurikulum Merdeka
              </p>
              <h1
                className="rise mt-2 text-[2.1rem] font-bold leading-[1.1] sm:text-5xl lg:text-6xl"
                style={delay(90)}
              >
                Susun modul ajar dari{" "}
                <Mark draw="load" delay={800}>
                  Capaian Pembelajaran
                </Mark>{" "}
                yang resmi.
              </h1>
              <p className="rise mt-6 max-w-xl text-base text-ink-soft sm:text-lg" style={delay(200)}>
                Pilih kelas, mata pelajaran, dan topik. SARPEBE membaca dokumen CP yang diunggah administrator,
                menyusun draf modul ajar, lalu mencantumkan halaman rujukannya. Anda tinggal menyunting dan
                mengunduh PDF.
              </p>
              <div className="rise mt-8 flex flex-col gap-3 min-[480px]:flex-row" style={delay(310)}>
                <Link href="/register" className={buttonVariants({ size: "lg" })}>
                  Buat akun
                </Link>
                <Link href="/login" className={buttonVariants({ size: "lg", variant: "outline" })}>
                  Sudah punya akun? Masuk
                </Link>
              </div>
            </div>

            <figure className="rise" style={delay(260)}>
              <figcaption className="mb-2 font-hand text-xl text-ink-soft">Contoh hasil</figcaption>
              <Sheet margin className="py-6 pr-5 sm:pr-8">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-semibold">Kelas 9</span>
                  <FaseTag grade="9" />
                  <span className="text-ink-soft">IPS</span>
                </div>
                <h2 className="mt-2 text-xl font-bold leading-tight sm:text-2xl">Pelaku dan kegiatan ekonomi</h2>

                <h3 className="mt-6 text-sm font-semibold uppercase tracking-wide text-ink-soft">Tujuan pembelajaran</h3>
                <p className="mt-2 leading-7">
                  Peserta didik mampu{" "}
                  <Mark draw="load" delay={1150}>
                    menganalisis interaksi antarpelaku ekonomi
                  </Mark>{" "}
                  dalam kegiatan produksi, distribusi, dan konsumsi.
                </p>
                <p className="mt-1 font-hand text-lg text-margin-text">kutipan dari CP, halaman 14</p>

                <h3 className="mt-6 text-sm font-semibold uppercase tracking-wide text-ink-soft">Sumber rujukan</h3>
                <p className="mt-2 text-sm">
                  <Mark draw="load" delay={1500}>
                    Dokumen CP IPS, hlm. 14
                  </Mark>
                </p>
              </Sheet>
            </figure>
          </div>
        </section>

        {/* Phases: real structure of the curriculum, and the same label shown across the app. */}
        <section id="fase" aria-labelledby="fase-judul" className="mx-auto w-full max-w-6xl px-5 py-12 sm:py-16 sm:px-6 lg:px-8 lg:py-20">
          <Reveal>
            <h2 id="fase-judul" className="max-w-2xl text-2xl font-bold sm:text-3xl lg:text-4xl">
              Kelas berapa masuk fase mana?
            </h2>
            <p className="mt-4 max-w-2xl text-ink-soft sm:text-lg">
              Capaian Pembelajaran disusun per fase, bukan per kelas. Ketik kelas Anda untuk melihat fasenya;
              label Fase juga tampil di samping kelas di seluruh SARPEBE.
            </p>
          </Reveal>
          <Reveal className="mt-8" delay={120}>
            <FaseFinder />
          </Reveal>
        </section>

        {/* How it works: a real sequence, so the numbers carry information. */}
        <section id="cara-kerja" aria-labelledby="cara-kerja-judul" className="border-y border-rule bg-sheet">
          <div className="mx-auto w-full max-w-6xl px-5 py-12 sm:py-16 sm:px-6 lg:px-8 lg:py-24">
            <Reveal>
              <h2 id="cara-kerja-judul" className="max-w-2xl text-2xl font-bold sm:text-3xl lg:text-4xl">
                Tiga langkah, tanpa mulai dari halaman kosong.
              </h2>
            </Reveal>
            <ol className="mt-10 divide-y divide-rule border-y border-rule">
              {STEPS.map((step, index) => (
                <Reveal
                  as="li"
                  key={step.title}
                  delay={index * 100}
                  className="grid gap-2 py-6 md:grid-cols-[4rem_minmax(0,1fr)_minmax(0,1.3fr)] md:items-baseline md:gap-8"
                >
                  <span aria-hidden className="font-hand text-5xl leading-none text-ballpoint">{index + 1}</span>
                  <h3 className="text-lg font-semibold sm:text-xl">{step.title}</h3>
                  <p className="text-ink-soft">{step.body}</p>
                </Reveal>
              ))}
            </ol>
          </div>
        </section>

        {/* Why it can be reviewed, then what the result looks like. */}
        <section id="sumber-rujukan" aria-labelledby="sumber-rujukan-judul">
          <div className="mx-auto grid w-full max-w-6xl gap-10 px-5 py-12 sm:py-16 sm:px-6 lg:px-8 lg:grid-cols-2 lg:py-24">
            <Reveal>
              <h2 id="sumber-rujukan-judul" className="text-2xl font-bold sm:text-3xl lg:text-4xl">
                Setiap modul menyebut sumbernya.
              </h2>
              <p className="mt-5 max-w-lg text-ink-soft sm:text-lg">
                Kepala sekolah atau pengawas bisa memeriksa dari mana sebuah tujuan pembelajaran berasal.
                Rujukan ditampilkan sebagai nama dokumen dan halaman, ditandai seperti stabilo di bagian{" "}
                <Mark draw="view" delay={300}>
                  Sumber rujukan
                </Mark>
                .
              </p>
            </Reveal>
            <dl className="divide-y divide-rule border-y border-rule">
              {TRUST_POINTS.map((point, index) => (
                <Reveal key={point.term} delay={index * 100} className="py-5">
                  <dt className="text-lg font-semibold">{point.term}</dt>
                  <dd className="mt-1 text-ink-soft">{point.detail}</dd>
                </Reveal>
              ))}
            </dl>
          </div>

          <div className="mx-auto w-full max-w-6xl px-5 pb-12 sm:pb-16 sm:px-6 lg:px-8 lg:pb-24">
            <Reveal>
              <SampleModule />
            </Reveal>
          </div>
        </section>

        {/* Administrators. */}
        <section id="administrator" aria-labelledby="administrator-judul" className="border-y border-rule bg-sheet">
          <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-12 sm:py-16 sm:px-6 lg:px-8 lg:grid-cols-2 lg:items-start lg:py-24">
            <Reveal>
              <h2 id="administrator-judul" className="text-2xl font-bold sm:text-3xl lg:text-4xl">
                Untuk administrator kurikulum
              </h2>
              <p className="mt-5 max-w-lg text-ink-soft sm:text-lg">
                Dokumen yang Anda unggah menjadi satu-satunya sumber modul ajar. Karena itu, label kelas dan
                mata pelajarannya perlu tepat.
              </p>
              <Link href="/login" className={buttonVariants({ variant: "outline", className: "mt-6" })}>
                Masuk sebagai administrator
              </Link>
            </Reveal>
            <ul className="space-y-4 text-base sm:text-lg">
              {ADMIN_POINTS.map((point, index) => (
                <Reveal as="li" key={point} delay={index * 100} className="flex gap-3">
                  <span aria-hidden className="mt-2.5 size-1.5 shrink-0 rounded-full bg-margin sm:mt-3" />
                  {point}
                </Reveal>
              ))}
            </ul>
          </div>
        </section>

        {/* Questions teachers ask before trusting a draft. */}
        <section id="pertanyaan-umum" aria-labelledby="pertanyaan-judul" className="mx-auto w-full max-w-6xl px-5 py-12 sm:py-16 sm:px-6 lg:px-8 lg:py-24">
          <div className="grid gap-8 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] lg:gap-16">
            <Reveal>
              <h2 id="pertanyaan-judul" className="text-2xl font-bold sm:text-3xl lg:text-4xl">
                Pertanyaan yang sering muncul
              </h2>
              <p className="mt-4 max-w-md text-ink-soft sm:text-lg">
                Jawabannya sesuai dengan cara SARPEBE bekerja saat ini.
              </p>
            </Reveal>
            <FaqList />
          </div>
        </section>

        <section className="border-t border-rule bg-wash">
          <Reveal className="mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-5 py-10 sm:px-6 sm:py-14 lg:px-8 md:flex-row md:items-center md:justify-between">
            <p className="max-w-xl text-xl font-bold leading-snug sm:text-2xl lg:text-3xl">
              Mulai dari satu topik yang akan Anda ajarkan minggu ini.
            </p>
            <Link href="/register" className={buttonVariants({ size: "lg", className: "w-full min-[480px]:w-auto" })}>
              Buat akun
            </Link>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-rule bg-paper">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-8 text-sm text-ink-soft sm:px-6 lg:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
            <Wordmark className="text-base" />
            <span>Sistem Automasi Rencana Pembelajaran Berbasis Kurikulum</span>
          </div>
          <nav aria-label="Tautan kaki" className="flex flex-wrap gap-x-6 gap-y-0.5">
            {LANDING_MENU.map((item) => (
              <a key={item.id} href={`#${item.id}`} className="inline-block py-1.5 underline-offset-4 hover:underline">
                {item.label}
              </a>
            ))}
            <Link href="/login" className="inline-block py-1.5 underline-offset-4 hover:underline">Masuk</Link>
            <Link href="/register" className="inline-block py-1.5 underline-offset-4 hover:underline">Buat akun</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
