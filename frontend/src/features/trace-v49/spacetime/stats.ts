import type { TraceAggregate, TraceSpacetimeDataset } from "./types";

export function spacetimeStats(dataset: TraceSpacetimeDataset): TraceAggregate {
  return Object.freeze({ ...dataset.aggregate });
}
