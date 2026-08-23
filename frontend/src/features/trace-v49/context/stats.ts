import type { TraceContextDataset } from "./types";

export interface TraceContextStats {
  readonly denominator: number;
  readonly controlledAssignments: number;
  readonly curatedMemberships: number;
  readonly acceptedSemanticEdges: number;
  readonly unknownCount: number;
}

export function contextStats(dataset: TraceContextDataset): TraceContextStats {
  return Object.freeze({
    denominator: dataset.counts.denominator,
    controlledAssignments: dataset.controlledAssignments.length,
    curatedMemberships: dataset.curatedMemberships.length,
    acceptedSemanticEdges: dataset.semanticEdges.length,
    unknownCount: dataset.missingness.unknownCount,
  });
}
