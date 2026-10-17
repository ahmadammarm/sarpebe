import { FaseTag } from "@/components/brand/FaseTag";
import { Mark } from "@/components/brand/Mark";
import { Sheet } from "@/components/brand/Sheet";

const ACTIVITIES = [
  { stage: "Pendahuluan", minutes: "15", description: "Guru mengajak peserta didik menyebutkan pelaku ekonomi yang mereka temui hari ini." },
  { stage: "Inti", minutes: "40", description: "Diskusi kelompok: memetakan alur produksi, distribusi, dan konsumsi satu barang." },
  { stage: "Inti", minutes: "20", description: "Presentasi peta alur, lalu umpan balik antarkelompok." },
  { stage: "Penutup", minutes: "5", description: "Setiap peserta didik menulis satu hal yang berubah dalam cara mereka memandang pasar." },
];

const RUBRIC = [
  { criterion: "Ketepatan peta alur", good: "Semua tahap benar dan berurutan", fair: "Satu tahap keliru" },
  { criterion: "Kerja sama kelompok", good: "Semua anggota berperan", fair: "Sebagian anggota berperan" },
];

const MATERIALS = ["Buku teks IPS kelas 9", "Data pasar tradisional setempat", "Lembar kerja peserta didik"];

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h4 className="text-sm font-semibold uppercase tracking-wide text-ink-soft">{children}</h4>;
}

/** A whole lesson plan as the result looks, clearly labelled as an example. */
export function SampleModule() {
  return (
    <figure className="mx-auto w-full max-w-3xl">
      <figcaption className="mb-2 font-hand text-xl text-ink-soft">Contoh modul ajar lengkap</figcaption>

      <Sheet margin className="py-7 pr-5 sm:pr-10">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="font-semibold">Kelas 9</span>
          <FaseTag grade="9" />
          <span className="text-ink-soft">IPS</span>
        </div>
        <h3 className="mt-2 text-2xl font-bold leading-tight sm:text-3xl">
          Pelaku dan Kegiatan Ekonomi di Sekitar Kita
        </h3>

        <div className="mt-7 space-y-8">
          <section aria-label="Tujuan pembelajaran">
            <SectionTitle>Tujuan pembelajaran</SectionTitle>
            <ul className="mt-3 space-y-3 leading-7">
              <li>
                Peserta didik mampu{" "}
                <Mark draw="view" delay={150}>
                  menganalisis interaksi antarpelaku ekonomi
                </Mark>{" "}
                dalam kegiatan produksi, distribusi, dan konsumsi.
                <span className="mt-0.5 block font-hand text-lg leading-snug text-margin-text">
                  kutipan dari CP, halaman 14
                </span>
              </li>
              <li>Peserta didik mampu menyajikan contoh kegiatan ekonomi di lingkungan sekitar.</li>
            </ul>
          </section>

          <section aria-label="Kegiatan pembelajaran">
            <SectionTitle>Kegiatan pembelajaran, pertemuan 1 (80 menit)</SectionTitle>
            <div className="mt-3 overflow-x-auto rounded-md border border-rule-strong">
              <table className="w-full min-w-[30rem] border-collapse text-left text-sm">
                <caption className="sr-only">Kegiatan pertemuan 1</caption>
                <thead className="bg-wash">
                  <tr>
                    <th scope="col" className="px-3 py-2 font-semibold">Tahap</th>
                    <th scope="col" className="px-3 py-2 font-semibold">Menit</th>
                    <th scope="col" className="px-3 py-2 font-semibold">Kegiatan</th>
                  </tr>
                </thead>
                <tbody>
                  {ACTIVITIES.map((activity) => (
                    <tr key={activity.description} className="border-t border-rule align-top">
                      <td className="px-3 py-2 font-semibold text-ballpoint">{activity.stage}</td>
                      <td className="px-3 py-2 tabular-nums">{activity.minutes}</td>
                      <td className="px-3 py-2">{activity.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="grid gap-8 sm:grid-cols-2">
            <section aria-label="Media dan sumber belajar">
              <SectionTitle>Media dan sumber belajar</SectionTitle>
              <ul className="mt-3 space-y-1.5">
                {MATERIALS.map((item) => (
                  <li key={item} className="flex gap-2.5">
                    <span aria-hidden className="mt-2.5 size-1.5 shrink-0 rounded-full bg-margin" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>

            <section aria-label="Asesmen">
              <SectionTitle>Asesmen</SectionTitle>
              <p className="mt-3">
                Formatif lewat presentasi peta alur, dengan rubrik berikut.
              </p>
            </section>
          </div>

          <section aria-label="Rubrik penilaian">
            <SectionTitle>Rubrik penilaian</SectionTitle>
            <div className="mt-3 overflow-x-auto rounded-md border border-rule-strong">
              <table className="w-full min-w-[30rem] border-collapse text-left text-sm">
                <caption className="sr-only">Rubrik penilaian presentasi</caption>
                <thead className="bg-wash">
                  <tr>
                    <th scope="col" className="px-3 py-2 font-semibold">Kriteria</th>
                    <th scope="col" className="px-3 py-2 font-semibold">3 (Baik)</th>
                    <th scope="col" className="px-3 py-2 font-semibold">2 (Cukup)</th>
                  </tr>
                </thead>
                <tbody>
                  {RUBRIC.map((row) => (
                    <tr key={row.criterion} className="border-t border-rule align-top">
                      <th scope="row" className="px-3 py-2 font-semibold">{row.criterion}</th>
                      <td className="px-3 py-2">{row.good}</td>
                      <td className="px-3 py-2">{row.fair}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section aria-label="Sumber rujukan">
            <SectionTitle>Sumber rujukan</SectionTitle>
            <ul className="mt-3 space-y-2 text-sm leading-7">
              <li>
                <Mark draw="view" delay={0}>
                  Dokumen CP IPS Fase D, hlm. 14
                </Mark>
              </li>
              <li>
                <Mark draw="view" delay={150}>
                  Dokumen CP IPS Fase D, hlm. 15
                </Mark>
              </li>
            </ul>
          </section>
        </div>
      </Sheet>

      <p className="mt-3 text-sm text-ink-soft">
        Ini contoh tampilan. Isi modul Anda mengikuti dokumen CP yang diunggah administrator.
      </p>
    </figure>
  );
}
