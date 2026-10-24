import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

// Only pages a visitor can open without an account. The areas behind sign-in are not listed.
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: `${SITE_URL}/`, changeFrequency: "monthly", priority: 1 },
    { url: `${SITE_URL}/login`, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE_URL}/register`, changeFrequency: "yearly", priority: 0.5 },
  ];
}
