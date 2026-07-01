import { defineConfig } from "astro/config";

// Static output. Pages query Postgres at build time (see src/lib/db.js).
export default defineConfig({
  site: process.env.PUBLIC_SITE_URL || "http://localhost",
  trailingSlash: "ignore",
});
