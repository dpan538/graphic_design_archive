import "server-only";

/* The fact layer (release pass, 2026-09-06). A v2 request names a state;
   this module resolves what that state actually shows from the authoritative
   reader of its surface — the public Search service, the governed Context
   projection, the Exploration V2 map through the view service, the Open
   Inquiry registry — and turns it into FACTS: the labels the note may use,
   the pairs it may name, the counts it may state, deterministic STATEMENTS
   the model composes from, the actions the page can really take, and one
   fingerprint over all of it. Nothing the client says about its facts is
   trusted; what it says it shows is checked against the facts. Only
   public-safe fields enter: no held record, no source text, no research
   note, no secret. */

import { createHash } from "node:crypto";
import { publicSearchStateHash } from "../search-v2/core";
import { searchPublicObjects } from "../search-v2/service.server";
import { lookupGovernedContextDataset } from "../trace-v49/context/governed/index.server";
import { retrieveExplorationView } from "../trace-v49/exploration-view/service.server";
import { retrieveOpenInquiry } from "../trace-v49/open-inquiry-v1/service.server";
import { SuggestionsInputError } from "./schema.server";
import type {
  ContextReference,
  ExplorationReference,
  InquiryReference,
  SearchReference,
  SystemSuggestionsRequestV2,
  SystemSuggestionSurface,
} from "./types";

export const SYSTEM_SUGGESTS_FACTS_VERSION = "gda-system-suggests-facts/v3";

export interface FactStatement {
  readonly id: string;
  readonly text: string;
}

export interface FactPair {
  readonly id: string;
  readonly a: string;
  readonly b: string;
  /* the association's accessible description, when the release allows it public */
  readonly description: string;
}

export interface SurfaceFacts {
  readonly surface: SystemSuggestionSurface;
  readonly factsVersion: typeof SYSTEM_SUGGESTS_FACTS_VERSION;
  /* the release and data version the facts were read from */
  readonly releaseVersion: string;
  /* SHA-256 over the canonical facts: the cache key's heart and the client's staleness check */
  readonly contextFingerprint: string;
  /* the surface's own state hash where one exists (Search); otherwise the fingerprint */
  readonly stateHash: string;
  readonly seedLabel: string | null;
  readonly labels: readonly string[];
  readonly pairs: readonly FactPair[];
  readonly counts: Readonly<Record<string, number>>;
  readonly statements: readonly FactStatement[];
  readonly validActionIds: readonly string[];
  /* what the model sees: the statements, the labels, the counts — never more */
  readonly publicContext: Readonly<Record<string, unknown>>;
  /* Search caches briefly; the governed surfaces longer */
  readonly cacheTtlMs: number;
  /* the Search aggregates, for the refinement candidates */
  readonly search?: {
    readonly filters: SearchReference["filters"];
    readonly topDecade: string | null;
    readonly topObjectType: string | null;
    readonly topTheme: string | null;
    readonly topMovement: string | null;
  };
}

const canonical = (value: unknown): string => JSON.stringify(value, (_key, item) => (item && typeof item === "object" && !Array.isArray(item) ? Object.fromEntries(Object.entries(item as Record<string, unknown>).sort(([l], [r]) => (l < r ? -1 : 1))) : item));
const fingerprintOf = (value: unknown): string => createHash("sha256").update(canonical(value)).digest("hex");
const fmt = (value: number): string => value.toLocaleString("en-US");
const capital = (value: string): string => value.charAt(0).toUpperCase() + value.slice(1);
const listOf = (items: readonly string[]): string => (items.length <= 1 ? items.join("") : `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`);
const NUMBER_WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"];
export const numberWord = (value: number): string => NUMBER_WORDS[value] ?? fmt(value);

function checkShown(shown: Readonly<Record<string, number>> | undefined, counts: Readonly<Record<string, number>>): void {
  if (!shown) return;
  for (const [key, value] of Object.entries(shown)) {
    if (!(key in counts)) throw new SuggestionsInputError("INVALID_ARGUMENT", `shown.${key} is not a fact of this surface`);
    if (counts[key] !== value) throw new SuggestionsInputError("INVALID_ARGUMENT", `shown.${key} (${value}) does not match the authoritative state (${counts[key]})`);
  }
}

function finish(facts: Omit<SurfaceFacts, "contextFingerprint" | "factsVersion" | "publicContext" | "stateHash"> & { readonly stateHash?: string }): SurfaceFacts {
  const core = { surface: facts.surface, releaseVersion: facts.releaseVersion, seedLabel: facts.seedLabel, labels: facts.labels, pairs: facts.pairs.map((pair) => [pair.id, pair.a, pair.b]), counts: facts.counts, statements: facts.statements, validActionIds: facts.validActionIds };
  const contextFingerprint = fingerprintOf(core);
  return {
    ...facts,
    factsVersion: SYSTEM_SUGGESTS_FACTS_VERSION,
    contextFingerprint,
    stateHash: facts.stateHash ?? contextFingerprint,
    publicContext: {
      surface: facts.surface,
      statements: facts.statements,
      labels: facts.labels,
      counts: facts.counts,
    },
  };
}

/* ---- SEARCH_RESULTS: the query, the filters, the exact count, the real aggregates ---- */
function searchFacts(reference: SearchReference, shown: SystemSuggestionsRequestV2["shown"]): SurfaceFacts {
  let result: ReturnType<typeof searchPublicObjects>;
  try {
    result = searchPublicObjects({ query: reference.query, filters: reference.filters, first: 1 });
  } catch (error) {
    throw new SuggestionsInputError("INVALID_ARGUMENT", error instanceof Error ? error.message : "The Search reference is invalid");
  }
  const total = result.pageInfo.totalExact;
  const summary = result.aggregateSummary;
  const counts: Record<string, number> = { exactResultCount: total };
  const statements: FactStatement[] = [];
  const labels: string[] = [];
  const filterWords: string[] = [];
  /* the query enters the statement only as plain words; markup, addresses or instructions stay out of the note */
  if (reference.query) {
    const plain = /^[\p{L}\p{N}\s'’\-.,&]{1,80}$/u.test(reference.query) && !/https?:|www\.|ignore|instruction|system prompt/iu.test(reference.query);
    filterWords.push(plain ? `the text "${reference.query}"` : "the entered text");
    /* the plain query is a supplied label: the note may quote it */
    if (plain) labels.push(reference.query);
  }
  for (const key of ["objectType", "theme", "movement"] as const) {
    const value = reference.filters[key];
    if (value) { filterWords.push(`the ${key === "objectType" ? "object type" : key} ${value}`); labels.push(value); }
  }
  if (reference.filters.yearFrom !== undefined || reference.filters.yearTo !== undefined) {
    const from = reference.filters.yearFrom; const to = reference.filters.yearTo;
    filterWords.push(from !== undefined && to !== undefined ? `the years ${from}–${to}` : from !== undefined ? `the years from ${from}` : `the years to ${to}`);
    if (from !== undefined) counts.yearFrom = from;
    if (to !== undefined) counts.yearTo = to;
  }
  const scope = filterWords.length ? ` for ${listOf(filterWords)}` : "";
  statements.push({ id: "S1", text: total === 0 ? `No public objects match this Search${scope}.` : `${fmt(total)} public ${total === 1 ? "object matches" : "objects match"} this Search${scope}.` });
  const top = (name: string, list: readonly { value: string; count: number }[], word: string): string | null => {
    const first = list[0];
    if (!first || total === 0) return null;
    counts[`${name}Count`] = first.count;
    labels.push(first.value);
    statements.push({ id: `S${statements.length + 1}`, text: `${fmt(first.count)} of the ${fmt(total)} matching objects ${first.count === 1 ? "is" : "are"} ${word === "decade" ? `dated to the ${first.value}` : `${word} ${first.value}`}.` });
    return first.value;
  };
  const topDecade = top("topDecade", summary.topDecades, "decade");
  const topObjectType = top("topObjectType", summary.topObjectTypes, "of the object type");
  const topTheme = top("topTheme", summary.topThemes, "under the theme");
  const topMovement = top("topMovement", summary.topMovements, "within the movement");
  checkShown(shown, counts);
  return finish({
    surface: "SEARCH_RESULTS",
    releaseVersion: `${result.release.id}:${result.release.searchIndexSha256.slice(0, 12)}:${result.release.algorithmVersion}`,
    stateHash: publicSearchStateHash({ query: result.query.text, filters: result.query.filters }),
    seedLabel: null,
    labels,
    pairs: [],
    counts,
    statements,
    validActionIds: [],
    cacheTtlMs: 5 * 60_000,
    search: { filters: result.query.filters, topDecade, topObjectType, topTheme, topMovement },
  });
}

/* ---- TRACE_CONTEXT: the object's governed context, on canvas or set aside; a dimension without terms is "not recorded" ---- */
const KIND_WORD = { medium: "medium", theme: "theme", movement_context: "movement context" } as const;
function contextFacts(reference: ContextReference, shown: SystemSuggestionsRequestV2["shown"]): SurfaceFacts {
  const lookup = lookupGovernedContextDataset(reference.objectId);
  if (!lookup.ok) throw new SuggestionsInputError("INVALID_ARGUMENT", lookup.code === "NOT_FOUND" ? "The Context object is not in the governed projection" : lookup.message);
  const dataset = lookup.data;
  /* the canvas names a representation by its governed id or by its term id */
  const byId = new Map<string, string>();
  for (const item of dataset.representations) { byId.set(item.id, item.id); byId.set(item.termId, item.id); }
  for (const id of reference.onCanvas) if (!byId.has(id)) throw new SuggestionsInputError("INVALID_ARGUMENT", "reference.onCanvas names a context this object does not carry");
  const onCanvas = new Set(reference.onCanvas.map((id) => byId.get(id) as string));
  const title = dataset.selectedRecord.title.trim() || dataset.selectedRecord.surfaceId;
  const labels: string[] = [title];
  const statements: FactStatement[] = [{ id: "C1", text: `The selected object is ${title}${dataset.selectedRecord.rootMetadata.objectType ? `, a ${dataset.selectedRecord.rootMetadata.objectType.toLowerCase()}` : ""}.` }];
  const counts: Record<string, number> = { representations: dataset.representations.length, onCanvas: onCanvas.size, setAside: dataset.representations.length - onCanvas.size };
  const validActionIds: string[] = [];
  for (const kind of ["medium", "theme", "movement_context"] as const) {
    const items = dataset.representations.filter((item) => item.kind === kind);
    counts[kind] = items.length;
    const shownItems = items.filter((item) => onCanvas.has(item.id));
    const aside = items.filter((item) => !onCanvas.has(item.id));
    counts[`${kind}OnCanvas`] = shownItems.length;
    counts[`${kind}SetAside`] = aside.length;
    for (const item of items) labels.push(item.label);
    const word = KIND_WORD[kind];
    if (items.length === 0) statements.push({ id: `C${statements.length + 1}`, text: `No ${word} is recorded for this object in the governed projection.` });
    else {
      const parts: string[] = [];
      if (shownItems.length) parts.push(`${listOf(shownItems.map((item) => item.label))} on the canvas`);
      if (aside.length) parts.push(`${listOf(aside.map((item) => item.label))} set aside`);
      statements.push({ id: `C${statements.length + 1}`, text: `${capital(word)}: ${parts.join("; ")}.` });
      if (aside.length) validActionIds.push(kind === "medium" ? "EXPAND_MEDIUM" : kind === "theme" ? "EXPAND_THEME" : "EXPAND_MOVEMENT");
    }
  }
  statements.push({ id: `C${statements.length + 1}`, text: `A context set aside is still recorded; it is out of the canvas, not out of the archive.` });
  checkShown(shown, counts);
  return finish({
    surface: "TRACE_CONTEXT",
    releaseVersion: `${dataset.release.researchReleaseId}:${dataset.release.contextProjectionSha256.slice(0, 12)}`,
    seedLabel: title,
    labels,
    pairs: [],
    counts,
    statements,
    validActionIds,
    cacheTtlMs: 30 * 60_000,
  });
}

/* ---- TRACE_VALIDATED_EXPLORATION: the visible terms and each visible association, by id and endpoints ---- */
function explorationFacts(reference: ExplorationReference, shown: SystemSuggestionsRequestV2["shown"]): SurfaceFacts {
  const view = retrieveExplorationView(reference.mapId, reference.stateId, undefined, undefined);
  if (!view.ok) throw new SuggestionsInputError("INVALID_ARGUMENT", view.code === "STATE_NOT_FOUND" || view.code === "INVALID_REQUEST" ? "The Exploration state is not a governed state" : view.message);
  const map = view.data.map;
  const labelOf = new Map(map.nodes.map((node) => [node.vocabulary_id, node.canonical_label]));
  const ordered = map.plain_text_tree.tree_node_ids.map((id) => labelOf.get(id) ?? "").filter(Boolean);
  const seed = view.data.starting_point.label;
  const pairs: FactPair[] = map.associations.map((item) => ({ id: item.association_id, a: item.endpoint_labels[0], b: item.endpoint_labels[1], description: item.association_accessible_description }));
  const counts: Record<string, number> = { visibleTerms: ordered.length, qualifiedAssociations: pairs.length };
  const statements: FactStatement[] = [];
  statements.push({ id: "E1", text: `This view shows ${numberWord(ordered.length)} ${ordered.length === 1 ? "term" : "terms"} and ${numberWord(pairs.length)} evidence-qualified generic ${pairs.length === 1 ? "association" : "associations"}.` });
  const others = ordered.filter((label) => label !== seed);
  if (others.length) statements.push({ id: "E2", text: `The visible terms are ${listOf(ordered)}.` });
  pairs.forEach((pair, index) => statements.push({ id: `E${index + 3}`, text: `In this view, ${pair.a} is paired with ${pair.b}.` }));
  checkShown(shown, counts);
  return finish({
    surface: "TRACE_VALIDATED_EXPLORATION",
    releaseVersion: `${map.database_snapshot}:${map.api_version}`,
    seedLabel: seed,
    labels: ordered,
    pairs,
    counts,
    statements,
    /* narration only: the rail carries the controls */
    validActionIds: [],
    cacheTtlMs: 30 * 60_000,
  });
}

/* ---- TRACE_OPEN_INQUIRY: the participants and the bounded scope of one inquiry; never its evidence text ---- */
function inquiryFacts(reference: InquiryReference, shown: SystemSuggestionsRequestV2["shown"]): SurfaceFacts {
  const result = retrieveOpenInquiry(reference.inquiryId);
  if (!result.ok) throw new SuggestionsInputError("INVALID_ARGUMENT", "The Open Inquiry is not in the public registry");
  const item = result.data.data.item;
  const participants = item.participants.map((participant) => participant.label);
  const counts: Record<string, number> = { participants: participants.length };
  const statements: FactStatement[] = [
    { id: "Q1", text: `This open inquiry considers a bounded question between ${listOf(participants)}.` },
    { id: "Q2", text: `Its scope: ${item.bounded_scope.trim().replace(/\.$/u, "")}.` },
    { id: "Q3", text: `The current evidence does not qualify this question for the validated graph.` },
    { id: "Q4", text: `Source details are not public in this release.` },
  ];
  checkShown(shown, counts);
  return finish({
    surface: "TRACE_OPEN_INQUIRY",
    releaseVersion: `${item.record_version}:${result.data.registry_sha256.slice(0, 12)}`,
    seedLabel: participants[0] ?? null,
    labels: participants,
    pairs: [],
    counts,
    statements,
    validActionIds: ["RETURN_TO_EXPLORATION", "REVIEW_SOURCE_BOUNDARY"],
    cacheTtlMs: 30 * 60_000,
  });
}

export function buildSurfaceFacts(request: SystemSuggestionsRequestV2): SurfaceFacts {
  switch (request.surface) {
    case "SEARCH_RESULTS": return searchFacts(request.reference as SearchReference, request.shown);
    case "TRACE_CONTEXT": return contextFacts(request.reference as ContextReference, request.shown);
    case "TRACE_VALIDATED_EXPLORATION": return explorationFacts(request.reference as ExplorationReference, request.shown);
    case "TRACE_OPEN_INQUIRY": return inquiryFacts(request.reference as InquiryReference, request.shown);
    default: throw new SuggestionsInputError("INVALID_ARGUMENT", `${request.surface} has no fact layer in this release`);
  }
}
