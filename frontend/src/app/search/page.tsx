import type { Metadata } from "next";
import { Suspense } from "react";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import SearchWorkspace from "@/features/search-v2/ui/SearchWorkspace";
import { publicSearchFacets } from "@/features/search-v2/service.server";

export const metadata: Metadata = {
  title: "Search the public v49 archive — Modern Graphic Design History",
  description: "Deterministic multilingual lexical search over 7,995 rights-safe public archive records.",
};

export default function SearchPage() {
  const facets = publicSearchFacets();
  return <ArchiveShell activeNav="search" mainScroll main={<Suspense fallback={<p className="read-platform" role="status">Loading Search…</p>}><SearchWorkspace facets={facets} /></Suspense>} />;
}
