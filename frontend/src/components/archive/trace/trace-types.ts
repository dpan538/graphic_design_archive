export type TraceLayer = "active" | "auxiliary" | "review";
export type TraceView = "atlas" | "constellation" | "object";

export interface AtlasCount {
  name: string;
  count: number;
}

export interface AtlasTreeCount {
  tree: string;
  count: number;
}

export interface AtlasRelation {
  label: string;
  family: RelationFamily;
  count: number;
}

export interface AtlasRegion {
  region: string;
  total: number;
  counts: number[];
  members?: string[];
}

export interface TraceAtlas {
  version: string;
  status: string;
  policy: {
    activeDefault: boolean;
    auxiliaryCountEligible: boolean;
    reviewMixedWithActive: boolean;
    influenceInferred: boolean;
    mediumGroupsAreDisplayFiltersOnly: boolean;
  };
  counts: {
    activeObjects: number;
    traceNodes: number;
    traceEdges: number;
    activeTrees: number;
    sourceVerified: number;
    metadataSupported: number;
    reviewObjects: number;
    auxiliaryObjects: number;
    influenceEdges: number;
  };
  decades: number[];
  decadeTotals: number[];
  regionMatrix: AtlasRegion[];
  atlasMarks: number;
  topSources: AtlasCount[];
  mediumGroups: AtlasCount[];
  relationTypes: AtlasRelation[];
  treeCounts: AtlasTreeCount[];
  assets: {
    catalog: string;
    review: string;
    auxiliary: string;
    neighborhoodBase: string;
  };
}

export interface ActiveCatalogItem {
  id: string;
  title: string;
  year: number;
  region: string;
  source: string;
  mediumGroup: string;
  tier: string;
  tree: string;
  shard: string;
  href: string;
  hrefKind: "object" | "source";
}

export interface ReviewCatalogItem {
  id: string;
  surfaceId: string;
  title: string;
  year: number | null;
  region: string;
  source: string;
  href: string;
  authorityState: string;
  traceState: string;
  reviewRoute: string;
  countPolicy: string;
  layer: "review";
}

export type RelationFamily =
  | "source_provenance"
  | "time_place"
  | "medium_context"
  | "historical_influence";

export interface TraceObject {
  id: string;
  nodeId: string;
  title: string;
  year: number;
  region: string;
  medium: string;
  mediumGroup: string;
  source: string;
  sourceUrl: string;
  href: string;
  hrefKind: "object" | "source";
  tree: string;
  traceState: string;
  traceTier: string;
  authorityState: string;
  evidenceReturnUrl: string;
  layer: "active" | "auxiliary";
  countEligible?: boolean;
  influenceState?: string;
}

export interface TraceNode {
  id: string;
  type: string;
  label: string;
  region: string;
  href: string;
  evidenceStatus: string;
  layer: "active" | "auxiliary";
}

export interface TraceEdge {
  id: string;
  label: string;
  family: RelationFamily;
  subject: string;
  object: string;
  direction: "incoming" | "outgoing" | "associated";
  branch?: string;
  evidenceUrl: string;
  evidenceText: string;
  evidenceField: string;
  confidence: string;
  reviewState: string;
  inferenceCheck: string;
}

export interface TraceGraph {
  object: TraceObject;
  nodes: TraceNode[];
  edges: TraceEdge[];
}

export interface CompactPayload {
  schema: string[];
  dictionaries: Record<string, string[]>;
  items: unknown[][];
}

export interface AuxiliaryPayload {
  version: string;
  layer: "auxiliary";
  countEligible: false;
  items: TraceGraph[];
}
