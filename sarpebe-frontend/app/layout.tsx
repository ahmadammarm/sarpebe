import type { Metadata } from "next";
import { Atkinson_Hyperlegible_Next, Bricolage_Grotesque, Caveat } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { themeInitScript } from "@/lib/theme-script";

// Display: sturdy, slightly quirky grotesque for headings.
const display = Bricolage_Grotesque({
  variable: "--next-font-display",
  subsets: ["latin"],
  display: "swap",
});

// Body: Atkinson Hyperlegible was designed for legibility; teachers read long documents on it.
const body = Atkinson_Hyperlegible_Next({
  variable: "--next-font-body",
  subsets: ["latin"],
  display: "swap",
});

// Margin notes only (short annotations next to content), never body text.
const hand = Caveat({
  variable: "--next-font-hand",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "SARPEBE",
    template: "%s | SARPEBE",
  },
  description:
    "Susun modul ajar dari Capaian Pembelajaran resmi, lengkap dengan halaman rujukannya.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className={`${display.variable} ${body.variable} ${hand.variable} font-sans antialiased`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
