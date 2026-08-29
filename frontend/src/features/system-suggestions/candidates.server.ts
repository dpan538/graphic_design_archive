import "server-only";

import { createHash } from "node:crypto";
import { publicSearchStateHash } from "../search-v2/core";
import { getPublicSearchIndex } from "../search-v2/index.server";
import { searchPublicObjects } from "../search-v2/service.server";
import type {
  ApprovedSuggestion,
  SearchSuggestionContext,
  SystemSuggestionSurface,
  SystemSuggestionsRequest,
  TraceSuggestionContext,
} from "./types";
import { SuggestionsInputError } from "./schema.server";

const TRACE_ACTIONS: Readonly<Record<Exclude<SystemSuggestionSurface, "SEARCH_RESULTS">, Readonly<Record<string, string>>>> = {
  TRACE_CONTEXT: {
    EXPAND_MEDIUM: "Review medium context",
    EXPAND_THEME: "Review theme context",
    EXPAND_MOVEMENT: "Review movement context",
    RETURN_TO_OBJECT: "Return to the selected object",
  },
  TRACE_SPACETIME: {
    NARROW_PERIOD: "Narrow the selected period",
    SELECT_GEOGRAPHY: "Select a geography",
    COMPARE_PUBLIC_COUNTS: "Compare public aggregate counts",
    RESET_VIEW: "Reset the spacetime view",
  },
  TRACE_VALIDATED_EXPLORATION: {
    FOCUS_VALIDATED_NODE: "Focus a validated node",
    REVIEW_VALIDATED_ASSOCIATION: "Review a validated association",
    RETURN_TO_COMPOSITION: "Return to the validated composition",
  },
  TRACE_OPEN_INQUIRY: {
    REVIEW_EVIDENCE_GAP: "Review the evidence gap",
    REVIEW_SOURCE_BOUNDARY: "Review the source boundary",
    RETURN_TO_VALIDATED_EXPLORATION: "Return to validated exploration",
  },
};

const idFor = (prefix: string, value: string) => `${prefix}-${createHash("sha256").update(value).digest("hex").slice(0, 12)}`;

function verifyAggregateValues(context: SearchSuggestionContext): void {
  const index = getPublicSearchIndex();
  const sets = {
    topObjectTypes: new Set(index.facets.object_types.map((item) => item.value)),
    topThemes: new Set(index.facets.themes.map((item) => item.value)),
    topMovements: new Set(index.facets.movements.map((item) => item.value)),
  };
  for (const field of Object.keys(sets) as (keyof typeof sets)[]) {
    for (const item of context.aggregates[field]) if (!sets[field].has(item.value)) throw new SuggestionsInputError("INVALID_ARGUMENT", `${field} contains a value outside the public Search dictionary`);
  }
  for (const key of ["objectType", "theme", "movement"] as const) {
    const value = context.filters[key];
    const set = key === "objectType" ? sets.topObjectTypes : key === "theme" ? sets.topThemes : sets.topMovements;
    if (value && !set.has(value)) throw new SuggestionsInputError("INVALID_ARGUMENT", `${key} is outside the public Search dictionary`);
  }
  for (const year of [context.filters.yearFrom, context.filters.yearTo]) {
    if (year !== undefined && (year < index.facets.year.min || year > index.facets.year.max)) throw new SuggestionsInputError("INVALID_ARGUMENT", "Search year is outside the public Search range");
  }
  for (const item of context.aggregates.topDecades) {
    const match = /^(\d{4})s$/.exec(item.value);
    const year = match ? Number(match[1]) : NaN;
    if (!Number.isInteger(year) || year < index.facets.year.min - 9 || year > index.facets.year.max) throw new SuggestionsInputError("INVALID_ARGUMENT", "topDecades contains a value outside the public Search year range");
  }
}

function searchCandidates(request: SystemSuggestionsRequest, context: SearchSuggestionContext): ApprovedSuggestion[] {
  verifyAggregateValues(context);
  const expectedHash = publicSearchStateHash({ query: context.query, filters: context.filters });
  if (request.stateHash !== expectedHash) throw new SuggestionsInputError("INVALID_ARGUMENT", "stateHash does not match the Search query and filters");
  const authoritative = searchPublicObjects({ query: context.query, filters: context.filters, first: 1 });
  const authoritativeAggregates = {
    topDecades: authoritative.aggregateSummary.topDecades,
    topObjectTypes: authoritative.aggregateSummary.topObjectTypes,
    topThemes: authoritative.aggregateSummary.topThemes,
    topMovements: authoritative.aggregateSummary.topMovements,
  };
  if (authoritative.pageInfo.totalExact !== context.exactResultCount || JSON.stringify(authoritativeAggregates) !== JSON.stringify(context.aggregates)) {
    throw new SuggestionsInputError("INVALID_ARGUMENT", "Search summary does not match the deterministic public result set");
  }
  const suggestions: ApprovedSuggestion[] = [];
  const addFilter = (key: "objectType" | "theme" | "movement", value: string, label: string) => {
    if (context.filters[key] === value) return;
    suggestions.push({ id: idFor(`search-${key}`, value), label, action: { kind: "SET_SEARCH_FILTER", parameters: { [key]: value } } });
  };
  const decade = context.aggregates.topDecades[0]?.value;
  if (decade) {
    const yearFrom = Number(decade.slice(0, 4));
    if (context.filters.yearFrom !== yearFrom || context.filters.yearTo !== yearFrom + 9) {
      suggestions.push({ id: idFor("search-year", decade), label: `Focus on ${decade}`, action: { kind: "SET_SEARCH_FILTER", parameters: { yearFrom, yearTo: yearFrom + 9 } } });
    }
  }
  const objectType = context.aggregates.topObjectTypes[0]?.value;
  if (objectType) addFilter("objectType", objectType, `Focus on ${objectType}`);
  const theme = context.aggregates.topThemes[0]?.value;
  if (theme) addFilter("theme", theme, `Use theme: ${theme}`);
  const movement = context.aggregates.topMovements[0]?.value;
  if (movement) addFilter("movement", movement, `Use movement: ${movement}`);
  for (const key of ["movement", "theme", "objectType"] as const) {
    if (context.filters[key]) suggestions.push({ id: `search-remove-${key}`, label: `Remove ${key.replace(/[A-Z]/g, (letter) => ` ${letter.toLowerCase()}`)} filter`, action: { kind: "REMOVE_SEARCH_FILTER", parameters: { field: key } } });
  }
  if (context.filters.yearFrom !== undefined || context.filters.yearTo !== undefined) suggestions.push({ id: "search-remove-year", label: "Remove year filter", action: { kind: "REMOVE_SEARCH_FILTER", parameters: { field: "year" } } });
  return suggestions.slice(0, 8);
}

function traceCandidates(surface: Exclude<SystemSuggestionSurface, "SEARCH_RESULTS">, context: TraceSuggestionContext): ApprovedSuggestion[] {
  const allowlist = TRACE_ACTIONS[surface];
  const expectedEvidence = surface === "TRACE_CONTEXT" ? "PUBLIC_CONTEXT"
    : surface === "TRACE_SPACETIME" ? "PUBLIC_AGGREGATE"
    : surface === "TRACE_VALIDATED_EXPLORATION" ? "VALIDATED"
    : "OPEN_INQUIRY";
  if (context.evidenceClass !== expectedEvidence) throw new SuggestionsInputError("INVALID_ARGUMENT", "evidenceClass does not match the TRACE surface");
  return [...new Set(context.validActionIds)]
    .filter((actionId) => Object.hasOwn(allowlist, actionId))
    .slice(0, 8)
    .map((actionId) => ({
      id: `trace-${surface.toLowerCase().replaceAll("_", "-")}-${actionId.toLowerCase().replaceAll("_", "-")}`,
      label: allowlist[actionId],
      action: { kind: "TRACE_ACTION" as const, parameters: { actionId } },
    }));
}

export function approvedCandidates(request: SystemSuggestionsRequest): ApprovedSuggestion[] {
  return request.surface === "SEARCH_RESULTS"
    ? searchCandidates(request, request.context as SearchSuggestionContext)
    : traceCandidates(request.surface, request.context as TraceSuggestionContext);
}
