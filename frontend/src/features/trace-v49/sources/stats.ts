import type { TraceSourcesDataset, TraceSourceItemKind } from "./types";

export interface TraceSourcesStats {
  readonly denominator: number;
  readonly itemCounts: Readonly<Record<TraceSourceItemKind, number>>;
  readonly sourceAssociations: number;
  readonly typedLinks: number;
  readonly acceptedSemanticEdges: number;
}

export function sourcesStats(dataset: TraceSourcesDataset): TraceSourcesStats {
  const itemCounts: Record<TraceSourceItemKind, number> = {
    source: 0,
    source_record: 0,
    evidence_occurrence: 0,
    claim: 0,
    citation: 0,
    locator: 0,
    provenance_activity: 0,
  };
  for (const item of dataset.sourceItems) itemCounts[item.kind] += 1;
  return Object.freeze({
    denominator: dataset.counts.denominator,
    itemCounts: Object.freeze(itemCounts),
    sourceAssociations: dataset.sourceAssociations.length,
    typedLinks: dataset.sourceLinks.length,
    acceptedSemanticEdges: dataset.semanticEdges.length,
  });
}
