export const TRACE_CONTEXT_PUBLIC_SCHEMA_VERSION = "trace-context/v1" as const;
export const TRACE_CONTEXT_PUBLIC_PROJECTION_ID = "trace-context-v1" as const;
export const TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION = "context-governance-v1" as const;
export const TRACE_CONTEXT_EXPLANATION_REGISTRY_VERSION = "trace-context-explanations-v1" as const;
export const TRACE_CONTEXT_GOVERNED_MAPPING_VERSION = "trace-context-governance-mapping-v1" as const;

export type PublicContextRepresentationKind =
  | "medium"
  | "theme"
  | "movement_context";

export type ContextRepresentationPublicationState =
  | "published"
  | "qualified";

export interface PublicContextRootMetadata {
  readonly creatorAttribution: string;
  readonly objectType: string;
  readonly dateDisplay: string;
  readonly sourceName: string;
}

export interface PublicContextSelectedRecord {
  readonly surfaceId: string;
  readonly title: string;
  readonly rootMetadata: PublicContextRootMetadata;
}

export interface GovernedContextSampleOption {
  readonly stableId: string;
  readonly title: string;
}

/* the object chooser (§7g): every public record with its title folded
   for search and its reader-facing verdict; the worked examples, picked
   by fixed criteria */
export interface GovernedContextObjectEntry {
  readonly stableId: string;
  readonly title: string;
  readonly folded: string;
  readonly readerFacing: boolean;
  readonly counts: Readonly<{ medium: number; theme: number; movement_context: number }>;
}

export type GovernedContextExampleRole = "three_contexts" | "medium_theme" | "two_themes" | "two_movements" | "other_language";

export interface GovernedContextExampleOption extends GovernedContextSampleOption {
  readonly role: GovernedContextExampleRole;
  readonly counts: Readonly<{ medium: number; theme: number; movement_context: number }>;
}


export interface PublicContextRepresentationProvenance {
  readonly provenanceId: string;
  readonly basis: "project_curated_typed_membership";
  readonly sourceKind: "medium" | "theme" | "movement";
  readonly sourceState: "proposed";
  readonly mappingPolicyVersion: typeof TRACE_CONTEXT_GOVERNED_MAPPING_VERSION;
  readonly governancePolicyVersion: typeof TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION;
  readonly decision: "PUBLISHED" | "QUALIFIED";
}

export interface PublicContextRepresentation {
  readonly id: string;
  readonly kind: PublicContextRepresentationKind;
  readonly termId: string;
  readonly label: string;
  readonly epistemicRole: "project_curated_context";
  readonly publicationState: ContextRepresentationPublicationState;
  readonly explanationCode: string;
  readonly provenance: PublicContextRepresentationProvenance;
}

export interface PublicContextExplanation {
  readonly explanationCode: string;
  readonly contextKind: PublicContextRepresentationKind;
  readonly publicLabel: string;
  readonly shortDefinition: string;
  readonly longDefinition: string;
  readonly sourceBasis: string;
  readonly derivationDescription: string;
  readonly permittedInterpretation: string;
  readonly prohibitedInterpretations: readonly string[];
  readonly governanceStatus: string;
  readonly connectionLabel: string;
  readonly uiShortExplanation: string;
  readonly methodPageExplanation: string;
  readonly accessibilityWording: string;
}

export interface PublicContextAccessibleValue {
  readonly label: string;
  readonly value: string;
}

export interface PublicContextAccessibleRow {
  readonly id: string;
  readonly category: "selected_record" | "context_representation";
  readonly label: string;
  readonly explanationCode: string | null;
  readonly values: readonly PublicContextAccessibleValue[];
}

export interface PublicContextDataset {
  readonly schemaVersion: typeof TRACE_CONTEXT_PUBLIC_SCHEMA_VERSION;
  readonly release: {
    readonly researchReleaseId: string;
    readonly researchManifestSha256: string;
    readonly contextProjectionId: typeof TRACE_CONTEXT_PUBLIC_PROJECTION_ID;
    readonly contextProjectionSha256: string;
  };
  readonly selectedRecord: PublicContextSelectedRecord;
  readonly availability: "ready" | "empty";
  readonly representations: readonly PublicContextRepresentation[];
  readonly counts: {
    readonly representations: number;
    readonly byKind: Readonly<{
      medium: number;
      theme: number;
      movementContext: number;
    }>;
  };
  readonly explanationRegistryVersion: typeof TRACE_CONTEXT_EXPLANATION_REGISTRY_VERSION;
  readonly explanations: readonly PublicContextExplanation[];
  readonly accessibleRows: readonly PublicContextAccessibleRow[];
}

export type GovernedContextLookupFailureCode =
  | "INVALID_ARGUMENT"
  | "NOT_FOUND"
  | "RELEASE_VERSION_MISMATCH"
  | "INTEGRITY_FAILURE";

export type GovernedContextLookup =
  | Readonly<{ ok: true; data: PublicContextDataset }>
  | Readonly<{
    ok: false;
    code: GovernedContextLookupFailureCode;
    message: string;
  }>;
