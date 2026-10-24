import type { NextConfig } from "next";
import { PRIVATE_PATHS } from "./lib/site";

const nextConfig: NextConfig = {
  // The dashboard pages are client components and cannot export `metadata`, so the header does it:
  // search engines must not index anything behind sign-in.
  async headers() {
    return PRIVATE_PATHS.map((path) => ({
      source: `${path}/:path*`,
      headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }],
    }));
  },
};

export default nextConfig;
