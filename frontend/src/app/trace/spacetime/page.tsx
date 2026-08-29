import type { Metadata } from "next";
import { isLikelyMobileTraceRequest, TraceDesktopRequired } from "@/features/trace-v49/mobile.server";
import styles from "./page.module.css";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Spacetime functional atlas — TRACE v49",
  description: "Unlinked governed Spacetime GIS and timeline functional foundation for TRACE v49.",
  robots: {
    index: false,
    follow: false,
  },
};

function Failure({ message }: Readonly<{ message: string }>) {
  return (
    <main className={styles.failure}>
      <p>TRACE v49 · fail-closed governed Spacetime workspace</p>
      <h1>Spacetime atlas unavailable</h1>
      <p role="alert">{message}</p>
      <p>No map projection or archive record payload was sent to the client.</p>
    </main>
  );
}

export default async function SpacetimePage() {
  if (await isLikelyMobileTraceRequest()) return <TraceDesktopRequired functionName="Spacetime" />;
  try {
    const [{ SpacetimeWorkspace }, spacetimeReader] = await Promise.all([
      import("@/features/trace-v49/spacetime/map"),
      import("@/features/trace-v49/spacetime/governed/reader.server"),
    ]);
    const { getGovernedSpacetimePeriodsDataset, lookupGovernedSpacetimeAtlas } = spacetimeReader;
    const periods = getGovernedSpacetimePeriodsDataset();
    const atlas = lookupGovernedSpacetimeAtlas(periods.defaultPeriodId);
    if (!atlas.ok) return <Failure message={atlas.message} />;
    return <SpacetimeWorkspace periods={periods} initialAtlas={atlas.data} />;
  } catch {
    return <Failure message="The governed Spacetime projection failed its integrity checks." />;
  }
}
