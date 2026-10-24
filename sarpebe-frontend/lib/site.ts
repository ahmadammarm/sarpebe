// Plain module (no "use client"): the root layout, sitemap and robots files import it on the server.

export const SITE_NAME = "SARPEBE";

export const SITE_DESCRIPTION =
  "Susun modul ajar dari Capaian Pembelajaran resmi, lengkap dengan halaman rujukannya.";

/** Public address of the site, without a trailing slash. Set NEXT_PUBLIC_SITE_URL in production. */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || process.env.NEXTAUTH_URL || "http://localhost:3000").replace(
  /\/+$/,
  ""
);

/** Areas behind sign-in. Search engines are told to stay out of them (robots.ts, next.config.ts). */
export const PRIVATE_PATHS = ["/lesson-plans", "/curriculum", "/profile", "/admin"] as const;
