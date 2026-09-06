import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  // The archive data module is intentionally large. Keep static generation
  // below the workstation/server memory-thrashing threshold and allow an
  // audited page enough time to finish instead of spawning retry storms.
  staticPageGenerationTimeout: 300,
  experimental: {
    cpus: 2,
    // Keep production startup bounded: eager entry preloading parses every
    // archival page chunk even when this process serves only the v3 API.
    preloadEntriesOnStart: false,
    staticGenerationMaxConcurrency: 1,
    staticGenerationMinPagesPerWorker: 100,
  },
  // Pin the file-tracing root to this app so an unrelated lockfile higher up
  // the filesystem is not picked as the workspace root.
  outputFileTracingRoot: path.join(__dirname),
  // Exploration v2 and v3 models are loaded at runtime rather than statically
  // imported, so include the governed data assets in standalone/server output.
  outputFileTracingIncludes: {
    "/*": [
      "./generated/trace-exploration-v2/production-read-model.json",
      "./generated/trace-exploration-v3/CHECKSUMS.sha256",
      "./generated/trace-exploration-v3/manifest.json",
      "./generated/trace-exploration-v3/read-model.json",
    ],
  },
  // Production-only: the dev server runs Turbopack (see package.json "dev"),
  // which does not read this hook. `next build` still uses Webpack, so the
  // cache setting below continues to apply where it was written for.
  webpack: (config, { dev, webpack }) => {
    if (!dev) {
      config.cache = false;
      // Retired studies import the pre-release mock corpus. Exclude their entire
      // dependency trees from production chunks, rather than hiding their links.
      config.plugins.push(new webpack.NormalModuleReplacementPlugin(
        /[\\/]src[\\/]app[\\/](?:contents|folders|main-sheets|sub-sheets|text-pages|cards|bookmarks|badges|slips|appendix|reading-notes|trace[\\/]types)(?:[\\/].*)?[\\/]page\.tsx$/,
        path.join(__dirname, "src/components/archive/ProductionUnavailablePage.tsx"),
      ));
    }
    return config;
  },
};

export default nextConfig;
