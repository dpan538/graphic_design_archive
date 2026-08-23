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
  TraceSourceAssociation,
  TraceUnknown,
} from "../domain";

export type TraceSourceItemKind =
  | "source"
  | "source_record"
  | "evidence_occurrence"
  | "claim"
  | "citation"
  | "locator"
  | "provenance_activity";

export interface TraceSourceItem {
  readonly id: string;
  readonly kind: TraceSourceItemKind;
  readonly ref: TracePublicDataRef;
  readonly evidenceRefs: readonly TraceEvidenceRef[];
}

export type TraceSourceLinkKind =
  | "record_from_source"
  | "evidence_occurrence"
  | "claim_support"
  | "claim_qualification"
  | "claim_challenge"
  | "citation"
  | "locator"
  | "provenance_activity";

export interface TraceSourceLink {
  readonly id: string;
  readonly kind: TraceSourceLinkKind;
  readonly from: TracePublicDataRef;
  readonly to: TracePublicDataRef;
  readonly evidenceRefs: readonly TraceEvidenceRef[];
}

export interface TraceSourcesInput extends TraceProjectionBaseInput {
  readonly sourceItems: readonly TraceSourceItem[];
  readonly sourceAssociations: readonly TraceSourceAssociation[];
  readonly sourceLinks: readonly TraceSourceLink[];
}

export interface TraceSourcesDataset {
  readonly domain: "sources";
  readonly release: TraceReleaseRef;
  readonly availability: TraceAvailabilityState;
  readonly selectedRecord: TracePublicDataRef;
  readonly sourceItems: readonly TraceSourceItem[];
  readonly sourceAssociations: readonly TraceSourceAssociation[];
  readonly sourceLinks: readonly TraceSourceLink[];
  readonly semanticEdges: readonly TraceSemanticEdge[];
  readonly unknowns: readonly TraceUnknown[];
  readonly missingness: TraceMissingness;
  readonly counts: TraceDatasetCounts;
  readonly warnings: readonly string[];
  readonly accessibleRows: readonly TraceAccessibleRow[];
}
