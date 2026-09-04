import type { Metadata } from "next";
import SiteNav from "@/components/site/SiteNav";
import { isLikelyMobileTraceRequest, TraceDesktopRequired } from "@/features/trace-v49/mobile.server";
import contextManifest from "../../../generated/trace-context-v1/manifest.json";
import spacetimeManifest from "../../../generated/trace-spacetime-v1/manifest.json";
import explorationManifest from "../../../generated/trace-exploration-v1/manifest.json";
import openInquiryRegistry from "../../../generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json";
import type { Baseline } from "./lib/content";
import TraceDesktop from "./desktop/TraceDesktop";

/* /trace — the shared entry to the three research environments (Context
   Canvas, Spacetime, Exploration). It is not a fourth function: it explains
   and organises the three. Desktop-only by policy (§4): a mobile request gets
   the desktop-required notice before any research runtime is imported. The
   baseline figures are read from the governed projections' manifests, never
   typed in. */

export const metadata: Metadata = {
  title: "TRACE",
  description:
    "The research environment of the Modern Graphic Design Archive: three views — Context Canvas, Spacetime, Exploration — over one governed public archive, with provenance and evidence boundaries kept in view.",
};

export default async function TracePage() {
  if (await isLikelyMobileTraceRequest()) {
    return (
      <>
        <SiteNav variant="mobile" active="trace" />
        <TraceDesktopRequired />
      </>
    );
  }
  const baseline: Baseline = {
    objects: contextManifest.counts.publicObjectCount,
    periods: spacetimeManifest.counts.timeBuckets,
    geographies: spacetimeManifest.counts.governedGeographyEntries,
    associations: explorationManifest.counts.qualified_associations,
    inquiries: openInquiryRegistry.records.length,
    yearFrom: spacetimeManifest.counts.earliestGovernedYear,
    yearTo: spacetimeManifest.counts.latestGovernedYear,
  };
  return <TraceDesktop baseline={baseline} />;
}
