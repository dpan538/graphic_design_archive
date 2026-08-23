import type {
  TraceAccessibleRow,
  TraceAvailabilityState,
  TraceDatasetCounts,
  TraceEvidenceRef,
  TraceMissingness,
  TraceProjectionBaseInput,
  TracePublicDataRef,
  TraceReleaseRef,
  TraceSemanticEdge,
  TraceUnknown,
} from "../domain";

export type TracePlaceRole =
  | "creation"
  | "publication"
  | "subject"
  | "collection"
  | "broad_region"
  | "recorded_context"
  | "unspecified";
export type TracePlacePrecision = "exact" | "city" | "country" | "region" | "broad_region" | "approximate" | "unknown";
export type TraceTimeRole =
  | "creation"
  | "publication"
  | "subject"
  | "collection"
  | "recorded_context"
  | "unspecified";
export type TraceTimePrecision = "day" | "month" | "year" | "range" | "approximate" | "unknown";

export interface TraceCoordinates {
  readonly latitude: number;
  readonly longitude: number;
  readonly provenance: "source" | "authority_registry" | "derived";
  readonly evidenceRef?: TraceEvidenceRef;
}

export interface TracePlaceObservation {
  readonly id: string;
  readonly place: TracePublicDataRef;
  readonly role: TracePlaceRole;
  readonly precision: TracePlacePrecision;
  readonly coordinates?: TraceCoordinates;
  readonly evidenceRefs: readonly TraceEvidenceRef[];
}

export interface TraceTimeObservation {
  readonly id: string;
  readonly time: TracePublicDataRef;
  readonly role: TraceTimeRole;
  readonly precision: TraceTimePrecision;
  readonly start?: string;
  readonly end?: string;
  readonly evidenceRefs: readonly TraceEvidenceRef[];
}

export interface TraceAggregate {
  readonly visibleCount: number;
  readonly denominator: number;
  readonly unknownCount: number;
  readonly unmappedCount: number;
}

export interface TraceSpacetimeInput extends TraceProjectionBaseInput {
  readonly places: readonly TracePlaceObservation[];
  readonly times: readonly TraceTimeObservation[];
  readonly aggregate: TraceAggregate;
}

export interface TraceSpacetimeDataset {
  readonly domain: "spacetime";
  readonly release: TraceReleaseRef;
  readonly availability: TraceAvailabilityState;
  readonly selectedRecord: TracePublicDataRef;
  readonly places: readonly TracePlaceObservation[];
  readonly times: readonly TraceTimeObservation[];
  readonly semanticEdges: readonly TraceSemanticEdge[];
  readonly unknowns: readonly TraceUnknown[];
  readonly aggregate: TraceAggregate;
  readonly missingness: TraceMissingness;
  readonly counts: TraceDatasetCounts;
  readonly warnings: readonly string[];
  readonly accessibleRows: readonly TraceAccessibleRow[];
}
