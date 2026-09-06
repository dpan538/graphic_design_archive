import { notFound } from "next/navigation";

// Production replacement for retired fixture/design-study entrypoints.
// The original studies and frozen research resources stay available locally.
export default function ProductionUnavailablePage(): never { notFound(); }
