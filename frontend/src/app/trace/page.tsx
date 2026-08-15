import type { Metadata } from "next";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { TraceReadSlice } from "@/components/archive/read-platform/ReadPlatformViews";

export const metadata: Metadata = {
  title: "TRACE evidence atlas — Modern Graphic Design History",
  description:
    "Object-local evidence routes and aggregate views for the selected sealed archive release.",
};

export default function TracePage() {
  return (
    <ArchiveShell
      activeNav="trace"
      main={<TraceReadSlice />}
      mainScroll
    />
  );
}
