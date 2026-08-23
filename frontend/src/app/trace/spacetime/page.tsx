import type { Metadata } from "next";
import { SpacetimeWorkspace } from "@/features/trace-v49/spacetime/map";
import {
  getGovernedSpacetimePeriodsDataset,
  lookupGovernedSpacetimeAtlas,
} from "@/features/trace-v49/spacetime/governed/reader.server";
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

export default function SpacetimePage() {
  try {
    const periods = getGovernedSpacetimePeriodsDataset();
    const atlas = lookupGovernedSpacetimeAtlas(periods.defaultPeriodId);
    if (!atlas.ok) return <Failure message={atlas.message} />;
    return <SpacetimeWorkspace periods={periods} initialAtlas={atlas.data} />;
  } catch {
    return <Failure message="The governed Spacetime projection failed its integrity checks." />;
  }
}
