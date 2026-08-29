import type { Metadata } from "next";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import TraceExplorationReference from "@/features/trace-v49/exploration-ui/TraceExplorationReference";
import { isLikelyMobileTraceRequest, TraceDesktopRequired } from "@/features/trace-v49/mobile.server";

export const metadata: Metadata = {
  title: "TRACE evidence atlas — Modern Graphic Design History",
  description:
    "Object-local evidence routes and aggregate views for the selected sealed archive release.",
};

export default async function TracePage() {
  if (await isLikelyMobileTraceRequest()) {
    return <ArchiveShell activeNav="trace" mainScroll main={<TraceDesktopRequired />} />;
  }
  const [{ listExplorationV3Collection }, { listOpenInquiries }] = await Promise.all([
    import("@/features/trace-v49/exploration-v3/service.server"),
    import("@/features/trace-v49/open-inquiry-v1/service.server"),
  ]);
  const concepts = listExplorationV3Collection("concepts");
  const associations = listExplorationV3Collection("associations");
  const compositions = listExplorationV3Collection("compositions");
  const inquiries = listOpenInquiries();
  if (!concepts.ok || !associations.ok || !compositions.ok || !inquiries.ok) {
    return <ArchiveShell activeNav="trace" mainScroll main={<main className="read-platform"><h1>TRACE unavailable</h1><p role="alert">The governed research projections failed closed.</p></main>} />;
  }
  const inquiryLabels = [...new Set(inquiries.data.data.items.flatMap((item) => item.participants.map((participant) => participant.label)))].slice(0, 12);
  return (
    <ArchiveShell
      activeNav="trace"
      main={<TraceExplorationReference
        validated={{
          conceptCount: concepts.data.data.count,
          associationCount: associations.data.data.count,
          compositionCount: compositions.data.data.count,
          labels: concepts.data.data.items.map((item) => item.canonical_label).slice(0, 12),
        }}
        openInquiry={{
          recordCount: inquiries.data.data.count,
          governedIdentityCount: inquiries.data.data.items.filter((item) => item.inquiry_only_association_identity !== null).length,
          labels: inquiryLabels,
        }}
      />}
      mainScroll
    />
  );
}
