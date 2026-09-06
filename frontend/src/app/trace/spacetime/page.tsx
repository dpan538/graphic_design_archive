import type { Metadata } from "next";
import Link from "next/link";
import SiteNav from "@/components/site/SiteNav";
import spacetimeManifest from "../../../../generated/trace-spacetime-v1/manifest.json";
import { SPACETIME_RELEASE_NOTE, SPACETIME_STATUS } from "../lib/content";
import styles from "./page.module.css";

/* /trace/spacetime — the release boundary (2026-09-05). Spacetime is not
   released in v49: the TRACE landing keeps its screen as a research
   direction under review, and this route states the boundary. Nothing
   of the Spacetime runtime is imported here — no workspace, no GIS, no
   governed reader, no System suggests; the projection, its readers, its
   API and its audits stay frozen as research infrastructure
   (docs/frontend/SPACETIME_RESEARCH_READINESS_CENSUS_v1.md). The two
   figures are read from the projection's manifest, never typed in. */

export const metadata: Metadata = {
  title: "Spacetime — TRACE",
  description: `Spacetime — ${SPACETIME_STATUS.toLowerCase()}. ${SPACETIME_RELEASE_NOTE}`,
  robots: { index: false, follow: false },
};

export default function SpacetimeBoundaryPage() {
  return (
    <>
      <SiteNav active="trace" />
      <main id="main" className={styles.boundary}>
        <p className={styles.eyebrow}>TRACE · Spacetime</p>
        <h1 className={styles.title}>{SPACETIME_STATUS}</h1>
        <p className={styles.lead}>{SPACETIME_RELEASE_NOTE}</p>
        <p className={styles.note}>
          Spacetime examines how recorded geographic context changes across time. The governed projection behind it — {spacetimeManifest.counts.timeBuckets} decade periods, {spacetimeManifest.counts.governedGeographyEntries} governed geographies — remains frozen as research infrastructure and is not mounted on any public page.
        </p>
        <p className={styles.back}>
          <Link href="/trace">Return to TRACE</Link>
        </p>
      </main>
    </>
  );
}
