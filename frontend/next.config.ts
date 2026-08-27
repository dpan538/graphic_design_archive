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
    staticGenerationMaxConcurrency: 1,
    staticGenerationMinPagesPerWorker: 100,
  },
  // Pin the file-tracing root to this app so an unrelated lockfile higher up
  // the filesystem is not picked as the workspace root.
  outputFileTracingRoot: path.join(__dirname),
  // The Exploration v2 model is loaded at runtime rather than statically
  // imported, so include the governed data asset in standalone/server output.
  outputFileTracingIncludes: {
    "/*": ["./generated/trace-exploration-v2/production-read-model.json"],
  },
  webpack: (config, { dev }) => {
    if (!dev) {
      config.cache = false;
    }
    return config;
  },
};

export default nextConfig;
