import type {
  TraceControlledAssignment,
  TraceCuratedMembership,
  TracePublicDataRef,
  TraceSemanticEdge,
} from "../../domain";

export const CONTEXT_CANVAS_SCHEMA_VERSION = 2 as const;
export const CONTEXT_CANVAS_HISTORY_LIMIT = 50;
export const CONTEXT_CANVAS_NODE_WIDTH = 224;
export const CONTEXT_CANVAS_NODE_HEIGHT = 104;
export const CONTEXT_CANVAS_MIN_ZOOM = 0.35;
export const CONTEXT_CANVAS_MAX_ZOOM = 2.5;
export const CONTEXT_CANVAS_DEFAULT_EXPORT_SCALE = 2;
export const CONTEXT_CANVAS_MAX_ABS_COORDINATE = 1_000_000;

export type ContextCanvasDataMode =
  | "synthetic_contract"
  | "real_v49_validation"
  | "governed_context_v1";

export type ContextCanvasRepresentationKind =
  | "medium"
  | "theme"
  | "movement_context";

export type ContextCanvasRepresentationSourceKind =
  | "medium"
  | "theme"
  | "movement";

export interface ContextCanvasRepresentationExplanation {
  readonly publicName: string;
  readonly definition: string;
  readonly longDefinition: string;
  readonly whyShown: string;
  readonly sourceBasis: string;
  readonly permittedInterpretation: string;
  readonly prohibitedInterpretations: readonly string[];
  readonly accessibilityWording: string;
}

export interface ContextCanvasRepresentationProvenance {
  readonly provenanceId: string;
  readonly basis: "project_curated_typed_membership";
  readonly sourceKind: ContextCanvasRepresentationSourceKind;
  readonly sourceState: "proposed";
  readonly mappingPolicyVersion: string;
  readonly governancePolicyVersion: "context-governance-v1";
  readonly decision:
    | "PUBLISHED"
    | "QUALIFIED";
}

export interface ContextCanvasGovernedRepresentation {
  readonly representationId: string;
  readonly termId: string;
  readonly kind: ContextCanvasRepresentationKind;
  readonly label: string;
  readonly epistemicRole: "project_curated_context";
  readonly publicationState: "published" | "qualified";
  readonly explanationCode: "CTX-MEDIUM" | "CTX-THEME" | "CTX-MOVEMENT";
  readonly connectionLabel: "classified as" | "themed as" | "curated within";
  readonly explanation: ContextCanvasRepresentationExplanation;
  readonly provenance: ContextCanvasRepresentationProvenance;
}

export interface ContextCanvasGovernedRootMetadata {
  readonly creatorAttribution: string;
  readonly objectType: string;
  readonly dateDisplay: string;
  readonly sourceName: string;
}

export interface ContextCanvasGovernedContextMetadata {
  readonly projectionId: string;
  readonly projectionSha256: string;
  readonly policyVersion: "context-governance-v1";
  readonly explanationRegistryVersion: string;
  readonly representations: readonly ContextCanvasGovernedRepresentation[];
  readonly rootMetadata?: ContextCanvasGovernedRootMetadata;
}

interface ContextCanvasDataMetadataBase {
  readonly dataLabel: string;
  readonly mappingVersion: string;
  readonly historicalEvidence: false;
  readonly publicObjectCohortCount: number;
}

export interface ContextCanvasUngovernedDataMetadata extends ContextCanvasDataMetadataBase {
  readonly candidateState: "synthetic_contract" | "not_published";
  readonly governedPublicRelease: false;
  readonly publicReleaseData: false;
  readonly governedContext?: never;
}

export interface ContextCanvasGovernedDataMetadata extends ContextCanvasDataMetadataBase {
  readonly candidateState: "published";
  readonly governedPublicRelease: true;
  readonly publicReleaseData: true;
  readonly governedContext: ContextCanvasGovernedContextMetadata;
}

export type ContextCanvasDataMetadata =
  | ContextCanvasUngovernedDataMetadata
  | ContextCanvasGovernedDataMetadata;

export type ContextCanvasTemplateId =
  | "context-overview"
  | "descriptive-context"
  | "curated-context"
  | "full-context";

export type ContextCanvasEntityId = string;

export interface ContextCanvasPosition {
  readonly x: number;
  readonly y: number;
}

export interface ContextCanvasViewport {
  readonly x: number;
  readonly y: number;
  readonly zoom: number;
}

export interface ContextCanvasViewportSize {
  readonly width: number;
  readonly height: number;
}

export interface ContextCanvasComposition {
  readonly templateId: ContextCanvasTemplateId;
  readonly templateVersion: number;
  readonly visibleEntityIds: readonly ContextCanvasEntityId[];
  readonly positions: Readonly<Record<ContextCanvasEntityId, ContextCanvasPosition>>;
}

export interface ContextCanvasControlledAssignmentConnection {
  readonly id: string;
  readonly connectionKind: "controlled_assignment";
  readonly sourceEntityId: ContextCanvasEntityId;
  readonly targetEntityId: ContextCanvasEntityId;
  readonly accessibleRowId: string;
  readonly assignment: TraceControlledAssignment;
}

export interface ContextCanvasContextRepresentationConnection {
  readonly id: string;
  readonly connectionKind: "context_representation";
  readonly sourceEntityId: ContextCanvasEntityId;
  readonly targetEntityId: ContextCanvasEntityId;
  readonly accessibleRowId: string;
  readonly representation: ContextCanvasGovernedRepresentation;
}

export interface ContextCanvasCuratedMembershipConnection {
  readonly id: string;
  readonly connectionKind: "curated_membership";
  readonly sourceEntityId: ContextCanvasEntityId;
  readonly targetEntityId: ContextCanvasEntityId;
  readonly accessibleRowId: string;
  readonly membership: TraceCuratedMembership;
}

export interface ContextCanvasSemanticConnection {
  readonly id: string;
  readonly connectionKind: "semantic_edge";
  readonly sourceEntityId: ContextCanvasEntityId;
  readonly targetEntityId: ContextCanvasEntityId;
  readonly accessibleRowId: string;
  readonly semanticEdge: TraceSemanticEdge;
}

export type ContextCanvasConnection =
  | ContextCanvasContextRepresentationConnection
  | ContextCanvasControlledAssignmentConnection
  | ContextCanvasCuratedMembershipConnection
  | ContextCanvasSemanticConnection;

export interface ContextCanvasConnectionGeometry {
  readonly connection: ContextCanvasConnection;
  readonly path: string;
  readonly labelX: number;
  readonly labelY: number;
  readonly accessibleLabel: string;
}

export interface ContextCanvasVisibleNode {
  readonly id: ContextCanvasEntityId;
  readonly ref: TracePublicDataRef;
  readonly position: ContextCanvasPosition;
  readonly isRoot: boolean;
  readonly representation?: ContextCanvasGovernedRepresentation;
}

export type ContextCanvasSelection =
  | Readonly<{ kind: "node"; id: ContextCanvasEntityId }>
  | Readonly<{ kind: "connection"; id: string }>
  | null;

export type ContextCanvasPhase =
  | "INITIALIZING"
  | "READY"
  | "EXPORTING"
  | "EXPORT_ERROR";

export type ContextCanvasInteraction =
  | Readonly<{ mode: "READY" }>
  | Readonly<{
    mode: "PALETTE_DRAGGING";
    entityId: ContextCanvasEntityId;
    pointerId: number;
  }>
  | Readonly<{
    mode: "NODE_DRAGGING";
    nodeId: ContextCanvasEntityId;
    pointerId: number;
    startClient: ContextCanvasPosition;
    originPosition: ContextCanvasPosition;
    baseline: ContextCanvasComposition;
  }>
  | Readonly<{
    mode: "PANNING";
    pointerId: number;
    startClient: ContextCanvasPosition;
    originViewport: ContextCanvasViewport;
  }>;

export interface ContextCanvasHistory {
  readonly past: readonly ContextCanvasComposition[];
  readonly present: ContextCanvasComposition;
  readonly future: readonly ContextCanvasComposition[];
}

export interface ContextCanvasState {
  readonly schemaVersion: typeof CONTEXT_CANVAS_SCHEMA_VERSION;
  readonly rootEntityId: ContextCanvasEntityId;
  readonly allowedEntityIds: readonly ContextCanvasEntityId[];
  readonly history: ContextCanvasHistory;
  readonly viewport: ContextCanvasViewport;
  readonly selection: ContextCanvasSelection;
  readonly phase: ContextCanvasPhase;
  readonly interaction: ContextCanvasInteraction;
  readonly statusMessage: string;
  readonly exportError: string | null;
}

export interface ContextCanvasBounds {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
  readonly empty: boolean;
}

export interface ContextCanvasExportSnapshot {
  readonly svg: string;
  readonly width: number;
  readonly height: number;
  readonly contentBounds: ContextCanvasBounds;
}

export function contextCanvasEntityId(ref: TracePublicDataRef): ContextCanvasEntityId {
  return `entity:${ref.kind}:${ref.stableId}`;
}

export function contextCanvasNodeDomId(entityId: ContextCanvasEntityId): string {
  return `context-canvas-node-${encodeURIComponent(entityId).replaceAll("%", "_")}`;
}

export function isFiniteCanvasPosition(value: unknown): value is ContextCanvasPosition {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ContextCanvasPosition>;
  return Number.isFinite(candidate.x)
    && Number.isFinite(candidate.y)
    && Math.abs(candidate.x as number) <= CONTEXT_CANVAS_MAX_ABS_COORDINATE
    && Math.abs(candidate.y as number) <= CONTEXT_CANVAS_MAX_ABS_COORDINATE;
}
