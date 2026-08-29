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

export type SystemSuggestionsRequest = {
  schemaVersion: "gda-system-suggestions-request/v1";
  surface: SystemSuggestionSurface;
  stateHash: string;
  context: SearchSuggestionContext | TraceSuggestionContext;
};

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
  stateHash: string;
  note: string;
  suggestions: readonly ApprovedSuggestion[];
  sourceClass: SuggestionSourceClass;
  promptVersion: string;
  providerStatus: string;
};
