import type { MetadataRoute } from "next";
import { getReaderEligibilityIndex } from "@/features/reader-eligibility/index.server";
import { site } from "@/features/machine-reading/project";
export default function sitemap(): MetadataRoute.Sitemap {
  return ["/", "/about", "/source", "/directory", "/read-api", ...Array.from(getReaderEligibilityIndex().byId).filter(([,x]) => x.eligibility === "INDEX_ELIGIBLE").map(([id]) => `/surfaces/${encodeURIComponent(id)}`)].map(path => ({ url: site + path }));
}
