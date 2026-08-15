import type { Metadata } from "next";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { SearchReadSlice } from "@/components/archive/read-platform/ReadPlatformViews";

export const metadata: Metadata = {
  title: "Search archive and TRACE — Modern Graphic Design History",
  description: "A full search workspace across published design records, active TRACE objects and normalized relation types.",
};

export default function SearchPage() {
  return <ArchiveShell activeNav="search" mainScroll main={<SearchReadSlice />} />;
}
