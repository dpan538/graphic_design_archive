import type {
  TraceAccessibleRow,
  TraceAvailabilityState,
  TraceControlledAssignment,
  TraceCuratedMembership,
  TraceDatasetCounts,
  TraceMissingness,
  TracePredicateDefinition,
  TraceProjectionBaseInput,
  TracePublicDataRef,
  TraceReleaseRef,
  TraceSemanticEdge,
  TraceUnknown,
} from "../domain";

export interface TraceContextInput extends TraceProjectionBaseInput {
  readonly controlledAssignments: readonly TraceControlledAssignment[];
  readonly curatedMemberships: readonly TraceCuratedMembership[];
}

export interface TraceContextDataset {
  readonly domain: "context";
  readonly release: TraceReleaseRef;
  readonly availability: TraceAvailabilityState;
  readonly selectedRecord: TracePublicDataRef;
  readonly items: readonly TracePublicDataRef[];
  readonly controlledAssignments: readonly TraceControlledAssignment[];
  readonly curatedMemberships: readonly TraceCuratedMembership[];
  readonly semanticEdges: readonly TraceSemanticEdge[];
  readonly unknowns: readonly TraceUnknown[];
  readonly missingness: TraceMissingness;
  readonly counts: TraceDatasetCounts;
  readonly warnings: readonly string[];
  readonly accessibleRows: readonly TraceAccessibleRow[];
}

export type { TracePredicateDefinition };
