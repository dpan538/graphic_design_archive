import type { TraceContextDataset } from "../types";

export const TRACE_CONTEXT_REALDATA_MAPPING_VERSION = "trace-context-realdata-v1" as const;

export type TraceContextValidationFolderType =
  | "medium"
  | "theme"
  | "movement"
  | "region";

export interface TraceContextValidationFolderCandidate {
  readonly folderToken: string;
  readonly folderType: TraceContextValidationFolderType;
  readonly label: string;
}

export interface TraceContextValidationRecordCandidate {
  readonly stableId: string;
  readonly title: string;
  readonly folders: readonly TraceContextValidationFolderCandidate[];
}

export interface TraceContextValidationMetadata {
  readonly dataMode: "real_v49_validation";
  readonly mappingVersion: typeof TRACE_CONTEXT_REALDATA_MAPPING_VERSION;
  readonly sourceReleaseTag: "v49-data-api-closure-20260821";
  readonly selectedPublicStableId: string;
  readonly candidateState: "not_published";
  readonly governedPublicRelease: false;
  readonly historicalEvidence: false;
  readonly publicReleaseData: false;
}

export interface TraceContextValidationProjection {
  readonly dataset: TraceContextDataset;
  readonly metadata: TraceContextValidationMetadata;
}

export type TraceContextValidationFailureCode =
  | "VALIDATION_DATA_NOT_GENERATED"
  | "RECORD_NOT_AVAILABLE"
  | "INVALID_RECORD_ID"
  | "VALIDATION_PROJECTION_ERROR"
  | "DATA_INTEGRITY_ERROR";

export interface TraceContextValidationFailure {
  readonly status: "error";
  readonly code: TraceContextValidationFailureCode;
  readonly message: string;
}

export interface TraceContextValidationReady {
  readonly status: "ready";
  readonly projection: TraceContextValidationProjection;
}

export type TraceContextValidationLookup =
  | TraceContextValidationReady
  | TraceContextValidationFailure;

export interface TraceContextValidationSampleOption {
  readonly stableId: string;
  readonly title: string;
}
