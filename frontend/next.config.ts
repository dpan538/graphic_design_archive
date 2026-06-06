import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  // Pin the file-tracing root to this app so an unrelated lockfile higher up
  // the filesystem is not picked as the workspace root.
  outputFileTracingRoot: path.join(__dirname),
  webpack: (config, { dev }) => {
    if (!dev) {
      config.cache = false;
    }
    return config;
  },
};

export default nextConfig;
