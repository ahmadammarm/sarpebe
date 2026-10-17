import { FaseTag } from "@/components/brand/FaseTag";
import { Mark } from "@/components/brand/Mark";
import { Sheet } from "@/components/brand/Sheet";

const ACTIVITIES = [
  { duration: "15 menit", description: "Pembukaan: guru mengajak peserta didik menyebutkan pelaku ekonomi yang mereka temui hari ini." },
  { duration: "40 menit", description: "Diskusi kelompok: memetakan alur produksi, distribusi, dan konsumsi satu barang." },
  { duration: "20 menit", description: "Presentasi peta alur, lalu umpan balik antarkelompok." },
  { duration: "15 menit", description: "Refleksi: setiap peserta didik menulis satu hal yang berubah dalam cara mereka memandang pasar." },
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
            <SectionTitle>Kegiatan pembelajaran</SectionTitle>
            <ul className="mt-3 divide-y divide-rule border-y border-rule">
              {ACTIVITIES.map((activity) => (
                <li key={activity.duration + activity.description} className="grid gap-1 py-3 sm:grid-cols-[6.5rem_minmax(0,1fr)] sm:gap-4">
                  <span className="text-sm font-semibold text-ballpoint">{activity.duration}</span>
                  <span>{activity.description}</span>
                </li>
              ))}
            </ul>
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
                Penilaian formatif lewat presentasi peta alur dan refleksi tertulis singkat.
              </p>
            </section>
          </div>

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
