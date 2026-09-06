import "server-only";

import {
  SYSTEM_SUGGESTION_SURFACES,
  type AggregateValue,
  type SearchSuggestionContext,
  type SystemSuggestionsInput,
  type SystemSuggestionsRequest,
  type SystemSuggestionsRequestV2,
  type TraceSuggestionContext,
} from "./types";

export class SuggestionsInputError extends Error {
  readonly code: "INVALID_ARGUMENT" | "REQUEST_TOO_LARGE";

  constructor(code: "INVALID_ARGUMENT" | "REQUEST_TOO_LARGE", message: string) {
    super(message);
    this.code = code;
  }
}

const MAX_REQUEST_BYTES = 16_384;
const SEARCH_KEYS = new Set(["query", "filters", "exactResultCount", "aggregates"]);
const TRACE_KEYS = new Set(["stateType", "labels", "counts", "validActionIds", "evidenceClass"]);
const FILTER_KEYS = new Set(["yearFrom", "yearTo", "objectType", "theme", "movement"]);
const AGGREGATE_KEYS = new Set(["topDecades", "topObjectTypes", "topThemes", "topMovements"]);

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new SuggestionsInputError("INVALID_ARGUMENT", `${label} must be an object`);
  return value as Record<string, unknown>;
}

function exactKeys(value: Record<string, unknown>, allowed: ReadonlySet<string>, label: string): void {
  for (const key of Object.keys(value)) if (!allowed.has(key)) throw new SuggestionsInputError("INVALID_ARGUMENT", `${label} contains unsupported field ${key}`);
}

function boundedString(value: unknown, label: string, maximum: number, allowEmpty = false): string {
  if (typeof value !== "string") throw new SuggestionsInputError("INVALID_ARGUMENT", `${label} must be a string`);
  const normalized = value.normalize("NFC").trim();
  if ((!allowEmpty && !normalized) || Array.from(normalized).length > maximum) throw new SuggestionsInputError("INVALID_ARGUMENT", `${label} is outside its length bound`);
  return normalized;
}

function boundedInteger(value: unknown, label: string, maximum = 7995): number {
  if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > maximum) throw new SuggestionsInputError("INVALID_ARGUMENT", `${label} must be a bounded non-negative integer`);
  return value as number;
}

function aggregateList(value: unknown, label: string): AggregateValue[] {
  if (!Array.isArray(value) || value.length > 5) throw new SuggestionsInputError("INVALID_ARGUMENT", `${label} must contain at most five values`);
  return value.map((item, index) => {
    const entry = record(item, `${label}[${index}]`);
    exactKeys(entry, new Set(["value", "count"]), `${label}[${index}]`);
    return { value: boundedString(entry.value, `${label}[${index}].value`, 160), count: boundedInteger(entry.count, `${label}[${index}].count`) };
  });
}

function searchContext(value: unknown): SearchSuggestionContext {
  const context = record(value, "context");
  exactKeys(context, SEARCH_KEYS, "context");
  const filters = record(context.filters, "context.filters");
  exactKeys(filters, FILTER_KEYS, "context.filters");
  const parsedFilters: SearchSuggestionContext["filters"] = {};
  for (const key of ["yearFrom", "yearTo"] as const) {
    if (filters[key] !== undefined) parsedFilters[key] = boundedInteger(filters[key], `context.filters.${key}`, 9999);
  }
  for (const key of ["objectType", "theme", "movement"] as const) {
    if (filters[key] !== undefined) parsedFilters[key] = boundedString(filters[key], `context.filters.${key}`, 160);
  }
  const aggregates = record(context.aggregates, "context.aggregates");
  exactKeys(aggregates, AGGREGATE_KEYS, "context.aggregates");
  return {
    query: boundedString(context.query, "context.query", 160, true),
    filters: parsedFilters,
    exactResultCount: boundedInteger(context.exactResultCount, "context.exactResultCount"),
    aggregates: {
      topDecades: aggregateList(aggregates.topDecades, "context.aggregates.topDecades"),
      topObjectTypes: aggregateList(aggregates.topObjectTypes, "context.aggregates.topObjectTypes"),
      topThemes: aggregateList(aggregates.topThemes, "context.aggregates.topThemes"),
      topMovements: aggregateList(aggregates.topMovements, "context.aggregates.topMovements"),
    },
  };
}

function traceContext(value: unknown): TraceSuggestionContext {
  const context = record(value, "context");
  exactKeys(context, TRACE_KEYS, "context");
  if (!Array.isArray(context.labels) || context.labels.length > 12) throw new SuggestionsInputError("INVALID_ARGUMENT", "context.labels must contain at most 12 labels");
  if (!Array.isArray(context.validActionIds) || context.validActionIds.length > 8) throw new SuggestionsInputError("INVALID_ARGUMENT", "context.validActionIds must contain at most eight actions");
  const counts = record(context.counts, "context.counts");
  if (Object.keys(counts).length > 8) throw new SuggestionsInputError("INVALID_ARGUMENT", "context.counts contains too many values");
  const parsedCounts: Record<string, number> = {};
  for (const [key, count] of Object.entries(counts)) parsedCounts[boundedString(key, "context.counts key", 48)] = boundedInteger(count, `context.counts.${key}`, 1_000_000);
  const evidenceClass = context.evidenceClass;
  if (!["PUBLIC_CONTEXT", "PUBLIC_AGGREGATE", "VALIDATED", "OPEN_INQUIRY"].includes(String(evidenceClass))) throw new SuggestionsInputError("INVALID_ARGUMENT", "context.evidenceClass is invalid");
  return {
    stateType: boundedString(context.stateType, "context.stateType", 80),
    labels: context.labels.map((label, index) => boundedString(label, `context.labels[${index}]`, 160)),
    counts: parsedCounts,
    validActionIds: context.validActionIds.map((action, index) => boundedString(action, `context.validActionIds[${index}]`, 80)),
    evidenceClass: evidenceClass as TraceSuggestionContext["evidenceClass"],
  };
}

/* v2: identifiers only — the reader's own ids, bounded and pattern-checked; the facts come from the server */
const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9:_\-.]{0,199}$/u;
function boundedId(value: unknown, label: string): string {
  const id = boundedString(value, label, 200);
  if (!ID_PATTERN.test(id)) throw new SuggestionsInputError("INVALID_ARGUMENT", `${label} has an invalid format`);
  return id;
}
function searchFilters(value: unknown): SearchSuggestionContext["filters"] {
  const filters = record(value, "reference.filters");
  exactKeys(filters, FILTER_KEYS, "reference.filters");
  const parsed: SearchSuggestionContext["filters"] = {};
  for (const key of ["yearFrom", "yearTo"] as const) if (filters[key] !== undefined) parsed[key] = boundedInteger(filters[key], `reference.filters.${key}`, 9999);
  for (const key of ["objectType", "theme", "movement"] as const) if (filters[key] !== undefined) parsed[key] = boundedString(filters[key], `reference.filters.${key}`, 160);
  return parsed;
}
function referenceFor(surface: SystemSuggestionsRequestV2["surface"], value: unknown): SystemSuggestionsRequestV2["reference"] {
  const reference = record(value, "reference");
  switch (surface) {
    case "SEARCH_RESULTS":
      exactKeys(reference, new Set(["query", "filters"]), "reference");
      return { query: boundedString(reference.query, "reference.query", 160, true), filters: searchFilters(reference.filters ?? {}) };
    case "TRACE_CONTEXT": {
      exactKeys(reference, new Set(["objectId", "onCanvas"]), "reference");
      if (!Array.isArray(reference.onCanvas) || reference.onCanvas.length > 64) throw new SuggestionsInputError("INVALID_ARGUMENT", "reference.onCanvas must list at most 64 ids");
      return { objectId: boundedId(reference.objectId, "reference.objectId"), onCanvas: reference.onCanvas.map((id, index) => boundedId(id, `reference.onCanvas[${index}]`)) };
    }
    case "TRACE_VALIDATED_EXPLORATION":
      exactKeys(reference, new Set(["mapId", "stateId"]), "reference");
      return { mapId: boundedId(reference.mapId, "reference.mapId"), stateId: boundedId(reference.stateId, "reference.stateId") };
    case "TRACE_OPEN_INQUIRY":
      exactKeys(reference, new Set(["inquiryId"]), "reference");
      return { inquiryId: boundedId(reference.inquiryId, "reference.inquiryId") };
    default:
      throw new SuggestionsInputError("INVALID_ARGUMENT", `${surface} takes no v2 reference`);
  }
}
function shownCounts(value: unknown): Readonly<Record<string, number>> | undefined {
  if (value === undefined) return undefined;
  const shown = record(value, "shown");
  if (Object.keys(shown).length > 8) throw new SuggestionsInputError("INVALID_ARGUMENT", "shown contains too many values");
  const parsed: Record<string, number> = {};
  for (const [key, count] of Object.entries(shown)) parsed[boundedString(key, "shown key", 48)] = boundedInteger(count, `shown.${key}`, 1_000_000);
  return parsed;
}

export function parseSystemSuggestionsRequest(value: unknown): SystemSuggestionsInput {
  const input = record(value, "request");
  if (input.schemaVersion === "gda-system-suggestions-request/v2") {
    exactKeys(input, new Set(["schemaVersion", "surface", "reference", "shown"]), "request");
    if (!SYSTEM_SUGGESTION_SURFACES.includes(input.surface as never)) throw new SuggestionsInputError("INVALID_ARGUMENT", "surface is unsupported");
    const surface = input.surface as SystemSuggestionsRequestV2["surface"];
    const shown = shownCounts(input.shown);
    return { schemaVersion: "gda-system-suggestions-request/v2", surface, reference: referenceFor(surface, input.reference), ...(shown ? { shown } : {}) };
  }
  exactKeys(input, new Set(["schemaVersion", "surface", "stateHash", "context"]), "request");
  if (input.schemaVersion !== "gda-system-suggestions-request/v1") throw new SuggestionsInputError("INVALID_ARGUMENT", "schemaVersion is unsupported");
  if (!SYSTEM_SUGGESTION_SURFACES.includes(input.surface as never)) throw new SuggestionsInputError("INVALID_ARGUMENT", "surface is unsupported");
  const surface = input.surface as SystemSuggestionsRequest["surface"];
  const stateHash = boundedString(input.stateHash, "stateHash", 256);
  if (!/^[A-Za-z0-9_-]{8,256}$/.test(stateHash)) throw new SuggestionsInputError("INVALID_ARGUMENT", "stateHash has an invalid format");
  return {
    schemaVersion: "gda-system-suggestions-request/v1",
    surface,
    stateHash,
    context: surface === "SEARCH_RESULTS" ? searchContext(input.context) : traceContext(input.context),
  };
}

export function parseBoundedJsonBody(serialized: string): SystemSuggestionsInput {
  if (Buffer.byteLength(serialized, "utf8") > MAX_REQUEST_BYTES) throw new SuggestionsInputError("REQUEST_TOO_LARGE", "request body exceeds 16384 bytes");
  try {
    return parseSystemSuggestionsRequest(JSON.parse(serialized));
  } catch (error) {
    if (error instanceof SuggestionsInputError) throw error;
    throw new SuggestionsInputError("INVALID_ARGUMENT", "request body must be valid JSON");
  }
}

export { MAX_REQUEST_BYTES };
