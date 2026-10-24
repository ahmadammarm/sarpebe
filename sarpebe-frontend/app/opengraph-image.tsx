import { ImageResponse } from "next/og";
import { SITE_NAME } from "@/lib/site";

export const alt = "SARPEBE: susun modul ajar dari Capaian Pembelajaran yang resmi";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// An image cannot use the Tailwind tokens, so these are the light-theme values of --paper, --ink,
// --ink-soft and --margin in app/globals.css. Change them together.
const PAPER = "#f5f7fc";
const INK = "#16213e";
const INK_SOFT = "#55627f";
const MARGIN = "#d13b3b";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: PAPER,
          color: INK,
        }}
      >
        <div style={{ width: 6, height: "100%", background: MARGIN, marginLeft: 96 }} />
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            flex: 1, // takes the rest of the width, so the padding on the right is kept and the headline wraps inside it
            padding: "0 96px 0 72px",
          }}
        >
          <div style={{ fontSize: 40, fontWeight: 700, letterSpacing: 4, color: INK_SOFT }}>{SITE_NAME}</div>
          <div style={{ marginTop: 28, fontSize: 76, fontWeight: 700, lineHeight: 1.1 }}>
            Susun modul ajar dari Capaian Pembelajaran yang resmi.
          </div>
          <div style={{ marginTop: 32, fontSize: 36, color: INK_SOFT }}>
            Lengkap dengan halaman rujukannya.
          </div>
        </div>
      </div>
    ),
    size
  );
}
