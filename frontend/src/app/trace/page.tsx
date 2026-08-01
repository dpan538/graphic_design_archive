import type { Metadata } from "next";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import TraceExplorer from "@/components/archive/trace/TraceExplorer";

export const metadata: Metadata = {
  title: "TRACE evidence atlas — Modern Graphic Design History",
  description:
    "Object-local evidence routes and aggregate time/geography views for the frozen v48 archive candidate.",
};

export default function TracePage() {
  return (
    <ArchiveShell
      activeNav="trace"
      main={<TraceExplorer />}
      mainScroll
    />
  );
}
