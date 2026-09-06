export const SYSTEM_SUGGESTION_SURFACES = [
  "SEARCH_RESULTS",
  "TRACE_CONTEXT",
  "TRACE_SPACETIME",
  "TRACE_VALIDATED_EXPLORATION",
  "TRACE_OPEN_INQUIRY",
] as const;

export type SystemSuggestionSurface = typeof SYSTEM_SUGGESTION_SURFACES[number];
export type SuggestionSourceClass = "MODEL" | "STATIC_FALLBACK" | "CURATED";

export type AggregateValue = { value: string; count: number };
export type SearchSuggestionContext = {
  query: string;
  filters: {
    yearFrom?: number;
    yearTo?: number;
    objectType?: string;
    theme?: string;
    movement?: string;
  };
  exactResultCount: number;
  aggregates: {
    topDecades: readonly AggregateValue[];
    topObjectTypes: readonly AggregateValue[];
    topThemes: readonly AggregateValue[];
    topMovements: readonly AggregateValue[];
  };
};

export type TraceSuggestionContext = {
  stateType: string;
  labels: readonly string[];
  counts: Readonly<Record<string, number>>;
  validActionIds: readonly string[];
  evidenceClass: "PUBLIC_CONTEXT" | "PUBLIC_AGGREGATE" | "VALIDATED" | "OPEN_INQUIRY";
};

/* v1: the client describes its state (kept for the frozen reference
   workspaces; a TRACE v1 context is never sent to the model) */
export type SystemSuggestionsRequest = {
  schemaVersion: "gda-system-suggestions-request/v1";
  surface: SystemSuggestionSurface;
  stateHash: string;
  context: SearchSuggestionContext | TraceSuggestionContext;
};

/* v2 (release pass, 2026-09-06): the client names its state; the server
   resolves the facts from the authoritative reader and checks the shown
   range against them */
export type SearchReference = {
  query: string;
  filters: SearchSuggestionContext["filters"];
};
export type ContextReference = {
  objectId: string;
  /* the representation ids standing on the canvas; the rest of the
     object's context is set aside */
  onCanvas: readonly string[];
};
export type ExplorationReference = {
  mapId: string;
  stateId: string;
};
export type InquiryReference = {
  inquiryId: string;
};
export type SystemSuggestionsReference = SearchReference | ContextReference | ExplorationReference | InquiryReference;

export type SystemSuggestionsRequestV2 = {
  schemaVersion: "gda-system-suggestions-request/v2";
  surface: SystemSuggestionSurface;
  reference: SystemSuggestionsReference;
  /* what the page shows, for the server to confirm: counts the reader can see */
  shown?: Readonly<Record<string, number>>;
};

export type SystemSuggestionsInput = SystemSuggestionsRequest | SystemSuggestionsRequestV2;

export type SuggestionAction = {
  kind: "SET_SEARCH_FILTER" | "REMOVE_SEARCH_FILTER" | "TRACE_ACTION";
  parameters: Readonly<Record<string, string | number>>;
};

export type ApprovedSuggestion = {
  id: string;
  label: string;
  action: SuggestionAction;
};

export type SystemSuggestionsResponse = {
  schemaVersion: "gda-system-suggestions-response/v1";
  surface: SystemSuggestionSurface;
  /* v1: the client's hash echoed; v2: the authoritative fingerprint (Search: the public search state hash) */
  stateHash: string;
  note: string;
  suggestions: readonly ApprovedSuggestion[];
  sourceClass: SuggestionSourceClass;
  promptVersion: string;
  providerStatus: string;
  /* v2: the server's fingerprint of the facts the note was written from,
     and the fact statements the model said it used */
  contextFingerprint?: string;
  usedFactIds?: readonly string[];
};
