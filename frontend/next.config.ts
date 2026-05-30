import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Pin the file-tracing root to this app so an unrelated lockfile higher up
  // the filesystem is not picked as the workspace root.
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
