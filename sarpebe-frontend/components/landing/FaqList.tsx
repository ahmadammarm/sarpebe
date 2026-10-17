import { Plus } from "lucide-react";
import { Reveal } from "@/components/brand/Reveal";

const QUESTIONS = [
  {
    question: "Dari mana isi modul berasal?",
    answer:
      "Dari dokumen CP, ATP, atau Buku Guru berformat PDF yang diunggah administrator. SARPEBE mencari bagian yang cocok dengan kelas, mata pelajaran, dan topik Anda, lalu menyusun modul dari bagian itu. Model diarahkan memakai hanya dokumen tersebut.",
  },
  {
    question: "Bagaimana jika dokumen untuk kelas dan mata pelajaran saya belum ada?",
    answer:
      "Penyusunan berhenti dan Anda diberi tahu bahwa dokumennya belum ada. Tidak ada modul yang dikarang tanpa sumber. Minta administrator mengunggah dokumen untuk kelas dan mata pelajaran itu.",
  },
  {
    question: "Apakah saya bisa mengubah hasilnya?",
    answer:
      "Bisa. Judul, tujuan, tabel kegiatan, rubrik, dan lampiran dapat disunting langsung di halaman, sel demi sel, lalu diunduh sebagai PDF. Sumber rujukan dicatat otomatis dan tidak bisa disunting.",
  },
  {
    question: "Apakah hasilnya pasti benar?",
    answer:
      "Tidak. Modul adalah draf yang dibantu oleh model bahasa, jadi bisa saja ada yang kurang tepat. Bandingkan dengan halaman rujukan yang tercantum, dan baca seluruhnya sebelum dipakai mengajar.",
  },
  {
    question: "Berapa lama modul disusun?",
    answer:
      "Biasanya 20 sampai 60 detik. Anda boleh menutup halaman selama proses berjalan; modul tetap tersimpan di daftar Modul ajar saya.",
  },
  {
    question: "Siapa yang bisa melihat modul saya?",
    answer:
      "Hanya Anda. Daftar modul menampilkan modul milik akun yang sedang masuk saja.",
  },
  {
    question: "Siapa yang bisa mengunggah dokumen kurikulum?",
    answer:
      "Hanya akun dengan peran administrator. Guru memakai dokumen yang sudah tersedia dan tidak mengelolanya.",
  },
];

/** Native <details> accordion: works without JavaScript and is keyboard accessible by default. */
export function FaqList() {
  return (
    <Reveal>
      <div className="divide-y divide-rule border-y border-rule">
        {QUESTIONS.map((item) => (
          <details key={item.question} className="group py-1">
            <summary className="flex cursor-pointer list-none items-start justify-between gap-6 rounded-sm py-4 text-lg font-semibold outline-none focus-visible:ring-3 focus-visible:ring-ring/40 [&::-webkit-details-marker]:hidden">
              <span>{item.question}</span>
              <Plus
                aria-hidden
                className="mt-1 size-5 shrink-0 text-ink-soft transition-transform duration-200 group-open:rotate-45"
              />
            </summary>
            <p className="max-w-2xl pb-4 text-ink-soft">{item.answer}</p>
          </details>
        ))}
      </div>
    </Reveal>
  );
}
