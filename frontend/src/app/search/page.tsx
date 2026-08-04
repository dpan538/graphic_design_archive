import type { Metadata } from "next";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import SearchWorkspace from "@/components/archive/search/SearchWorkspace";

export const metadata: Metadata = {
  title: "Search archive and TRACE — Modern Graphic Design History",
  description: "A full search workspace across archive surfaces, active TRACE objects and normalized relation types.",
};

export default function SearchPage() {
  return <ArchiveShell activeNav="search" mainScroll main={<SearchWorkspace />} />;
}
