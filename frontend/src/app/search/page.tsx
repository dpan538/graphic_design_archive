import type { Metadata } from "next";
import { Suspense } from "react";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import SearchWorkspace from "@/features/search-v49/ui/SearchWorkspace";

export const metadata: Metadata = {
  title: "Search the public v49 archive — Modern Graphic Design History",
  description: "Deterministic multilingual lexical search over 7,995 rights-safe public archive records.",
};

export default function SearchPage() {
  return <ArchiveShell activeNav="search" mainScroll main={<Suspense fallback={<p className="read-platform" role="status">Loading search…</p>}><SearchWorkspace /></Suspense>} />;
}
