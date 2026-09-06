import "server-only";

import { guidanceCacheKey, mergeInFlight, readGuidanceCache, readLastGoodGuidance, storeGuidance } from "./cache.server";
import { approvedCandidatesFromFacts, legacyTraceCandidates, MAX_ACTIONS, verifiedSearchReference } from "./candidates.server";
import { buildSurfaceFacts, type SurfaceFacts } from "./facts.server";
import {
  DEEPSEEK_DEFAULT_BASE_URL,
  DEEPSEEK_DEFAULT_MODEL,
  DeepSeekGuidanceProvider,
  EXPLORATION_NARRATION_MAX_ACTIONS,
  EXPLORATION_NARRATION_MAX_SENTENCES,
  EXPLORATION_NARRATION_MAX_WORDS,
  isExplorationNarration,
  legacyFallbackNote,
  modelConfigVersion,
  ProviderFailure,
  SPACETIME_GUIDANCE_MAX_ACTIONS,
  SPACETIME_GUIDANCE_MAX_SENTENCES,
  SPACETIME_GUIDANCE_MAX_WORDS,
  StaticFallbackProvider,
  SYSTEM_SUGGESTIONS_LANGUAGE,
  SYSTEM_SUGGESTIONS_MAX_SENTENCES,
  SYSTEM_SUGGESTIONS_MAX_WORDS,
  SYSTEM_SUGGESTIONS_PROMPT_VERSION,
  type ProviderDraft,
} from "./providers.server";
import { parseSystemSuggestionsRequest } from "./schema.server";
import type { ApprovedSuggestion, SystemSuggestionsInput, SystemSuggestionsRequest, SystemSuggestionsRequestV2, SystemSuggestionsResponse, TraceSuggestionContext } from "./types";

type Environment = Readonly<Record<string, string | undefined>>;
type ServiceDependencies = { environment?: Environment; fetchImpl?: typeof fetch; timeoutMsForTest?: number; now?: () => number };

export class UnsafeProviderOutput extends Error {}

export function environmentConfig(environment: Environment, timeoutMsForTest?: number) {
  const mode = environment.SYSTEM_SUGGESTIONS_PROVIDER?.trim().toLowerCase() || "auto";
  const rawTimeout = Number(environment.SYSTEM_SUGGESTIONS_TIMEOUT_MS ?? "2500");
  const timeoutMs = timeoutMsForTest ?? (Number.isFinite(rawTimeout) ? Math.min(5000, Math.max(250, Math.trunc(rawTimeout))) : 2500);
  const requestedBase = environment.DEEPSEEK_BASE_URL?.trim() || DEEPSEEK_DEFAULT_BASE_URL;
  const requestedModel = environment.DEEPSEEK_MODEL?.trim() || DEEPSEEK_DEFAULT_MODEL;
  const rawTemperature = Number(environment.SYSTEM_SUGGESTIONS_TEMPERATURE ?? "0");
  const temperature = Number.isFinite(rawTemperature) ? Math.min(1, Math.max(0, Math.round(rawTemperature * 100) / 100)) : 0;
  return {
    mode: ["auto", "static", "off", "deepseek"].includes(mode) ? mode : "auto",
    apiKey: environment.DEEPSEEK_API_KEY?.trim() ?? "",
    baseUrl: requestedBase === DEEPSEEK_DEFAULT_BASE_URL ? requestedBase : DEEPSEEK_DEFAULT_BASE_URL,
    model: requestedModel === DEEPSEEK_DEFAULT_MODEL ? requestedModel : DEEPSEEK_DEFAULT_MODEL,
    timeoutMs,
    temperature,
  };
}

/* ======================= the gate: facts, relations, numbers, claims ======================= */

const NUMBER_WORDS: Readonly<Record<string, number>> = { zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12 };
/* claims no surface may make: reasons, history, likelihood, strength, similarity, sources or records as counts, promises, absence */
const FORBIDDEN_ALL = /\b(?:influenc\w*|caus\w*|led to|leads? to|result(?:ed|s)? (?:in|from)|likely|probab\w*|possibl\w*|perhaps|maybe|suggest\w*|progress\w*|sequence|trajector\w*|indicat\w*|impl(?:y|ies|ied)|reflect\w*|reveal\w*|explain\w*|why|histor\w*|weak\w*|strong\w*|similar\w*|semantic\w*|co-?occur\w*|confiden\w*|sources?|evidence records?|records?|guarantee\w*|will (?:find|return|show|yield|give)|more results|does not exist|do not exist|never existed|no such|missing|absent|lost|undocumented|unknown|important|importance|significan\w*|origin\w*|develop\w*|evolv\w*)\b/iu;
const FORBIDDEN_EXPLORATION = /\b(?:earlier|later|before|after|then|subsequent\w*|precede\w*|follow\w*|chronolog\w*|century|decade|\d{4}s?|war|movement|designer|artist|nation\w*|countr\w*|cit(?:y|ies)|promot\w*|diffus\w*|spread\w*|circulat\w*|transmi\w*|hierarch\w*|central|dominant|add\w* to the (?:validated )?graph)\b/iu;
const FORBIDDEN_INQUIRY = /\b(?:is|are|as|became?|counts? as) (?:a |an |the )?validated\b|\bvalidated (?:historical )?(?:association|relation)\b(?![^.]*\bnot\b)/iu;
const PAIRING = /\b(?:pair(?:ed|s|ing)?|associat(?:ed|es|ion|ions)|connect(?:ed|s|ion|ions)?|link(?:ed|s)?|relat(?:ed|es|ion|ions)|between|with)\b/iu;
const COUNT_PHRASE = /\b(?:\w+[- ])?(?:evidence-qualified |qualified )?generic associations?\b|\bevidence-qualified generic associations?\b/giu;
const COVISIBLE = /\b(?:alongside|shown (?:here )?with|together with|appears? with|shown here)\b/iu;
const QUOTED = /["“]([^"”]+)["”]/gu;

const escape = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
function sentencesOf(note: string): string[] {
  return note.split(/(?<=[.!?])\s+/u).map((part) => part.trim()).filter(Boolean);
}
/* the supplied labels a sentence names, longest first so a label inside another counts once */
function labelsIn(sentence: string, labels: readonly string[]): { labels: string[]; positions: number[] } {
  const found: { label: string; at: number }[] = [];
  let masked = sentence;
  for (const label of [...labels].sort((l, r) => r.length - l.length)) {
    const pattern = new RegExp(`(?<![\\p{L}\\p{N}])${escape(label)}(?![\\p{L}\\p{N}])`, "iu");
    const match = pattern.exec(masked);
    if (!match) continue;
    found.push({ label, at: match.index });
    masked = `${masked.slice(0, match.index)}${" ".repeat(label.length)}${masked.slice(match.index + label.length)}`;
  }
  found.sort((l, r) => l.at - r.at);
  return { labels: found.map((item) => item.label), positions: found.map((item) => item.at) };
}
function numbersIn(text: string): number[] {
  const values: number[] = [];
  for (const digits of text.match(/\d[\d,]*/gu) ?? []) values.push(Number(digits.replace(/,/g, "")));
  for (const word of text.toLowerCase().match(/\b[a-z]+\b/gu) ?? []) if (word in NUMBER_WORDS) values.push(NUMBER_WORDS[word] as number);
  return values;
}
function allowedNumbers(facts: SurfaceFacts): Set<number> {
  const allowed = new Set<number>(Object.values(facts.counts));
  for (const statement of facts.statements) for (const value of numbersIn(statement.text)) allowed.add(value);
  for (const label of facts.labels) for (const value of numbersIn(label)) allowed.add(value);
  return allowed;
}

/* the reading of one note against its facts: throws UnsafeProviderOutput with the reason */
export function assertFactualNote(rawNote: string, facts: SurfaceFacts): string {
  const note = rawNote.normalize("NFC").trim();
  if (!note || Array.from(note).length > 320) throw new UnsafeProviderOutput("note length");
  if (/(?:https?:\/\/|www\.|\[[^\]]+\]\(|^#{1,6}\s|[*_`]{2,})/imu.test(note)) throw new UnsafeProviderOutput("note format");
  if (/\b(?:I|me|my|mine|we|our|ours|you should|please)\b/u.test(note)) throw new UnsafeProviderOutput("note voice");
  if (/%/u.test(note)) throw new UnsafeProviderOutput("percentage");
  const sentences = sentencesOf(note);
  if (sentences.length < 1 || sentences.length > SYSTEM_SUGGESTIONS_MAX_SENTENCES) throw new UnsafeProviderOutput("sentence count");
  if (note.split(/\s+/u).filter(Boolean).length > SYSTEM_SUGGESTIONS_MAX_WORDS) throw new UnsafeProviderOutput("word count");
  /* a disclaimer may name a claim only to deny it; the one permitted "because" is the inquiry's evidence */
  const asserted = note
    .replace(/\b(?:without (?:asserting|implying|claiming|suggesting)|rather than|not|neither|nor|never)\b[^.;]*/giu, " ")
    .replace(/\bbecause (?:its |the |current )?evidence[^.;]*/giu, " ");
  const forbiddenAll = FORBIDDEN_ALL.exec(asserted);
  if (forbiddenAll) throw new UnsafeProviderOutput(`forbidden claim: ${forbiddenAll[0]}`);
  if (facts.surface === "TRACE_VALIDATED_EXPLORATION" || facts.surface === "TRACE_OPEN_INQUIRY") {
    const forbidden = FORBIDDEN_EXPLORATION.exec(asserted);
    if (forbidden) throw new UnsafeProviderOutput(`forbidden claim: ${forbidden[0]}`);
  }
  if (facts.surface === "TRACE_OPEN_INQUIRY" && FORBIDDEN_INQUIRY.test(note)) throw new UnsafeProviderOutput("inquiry framed as validated");
  /* numbers: only the counts the facts state */
  const allowed = allowedNumbers(facts);
  for (const value of numbersIn(note)) if (!allowed.has(value)) throw new UnsafeProviderOutput(`unsupplied number ${value}`);
  /* quoted terms: only supplied labels */
  const lower = facts.labels.map((label) => label.toLowerCase());
  for (const quoted of note.match(QUOTED) ?? []) {
    const term = quoted.slice(1, -1).toLowerCase();
    if (!lower.some((label) => label === term || label.includes(term))) throw new UnsafeProviderOutput("unsupplied quoted term");
  }
  /* relations: a sentence that pairs names exactly one supplied pair; a co-visibility sentence may list the visible terms */
  const pairSet = new Set(facts.pairs.flatMap((pair) => [`${pair.a.toLowerCase()}|${pair.b.toLowerCase()}`, `${pair.b.toLowerCase()}|${pair.a.toLowerCase()}`]));
  for (const sentence of sentences) {
    const stripped = sentence.replace(COUNT_PHRASE, " ");
    const named = labelsIn(stripped, facts.labels);
    const pairs = stripped.match(new RegExp(PAIRING.source, "giu")) ?? [];
    if (facts.surface === "TRACE_VALIDATED_EXPLORATION") {
      const predicate = pairs.filter((word) => !/^with$/iu.test(word) || !COVISIBLE.test(stripped));
      if (predicate.length === 0) continue;
      if (named.labels.length === 0) continue;
      if (named.labels.length !== 2) throw new UnsafeProviderOutput(`pairing names ${named.labels.length} terms`);
      if (!pairSet.has(`${named.labels[0]?.toLowerCase()}|${named.labels[1]?.toLowerCase()}`)) throw new UnsafeProviderOutput(`pairing not shown: ${named.labels.join(" / ")}`);
    } else if (facts.surface === "TRACE_OPEN_INQUIRY") {
      const claims = pairs.filter((word) => !/^(?:between|with)$/iu.test(word));
      if (claims.length) throw new UnsafeProviderOutput(`inquiry asserts a relation: ${claims[0]}`);
    } else if (facts.surface === "TRACE_CONTEXT") {
      const claims = pairs.filter((word) => !/^(?:with|between)$/iu.test(word));
      if (claims.length && named.labels.length >= 2) throw new UnsafeProviderOutput(`context asserts a relation: ${claims[0]}`);
    }
  }
  return note;
}

function safeDraft(draft: ProviderDraft, facts: SurfaceFacts, candidates: readonly ApprovedSuggestion[]): ProviderDraft {
  const note = assertFactualNote(draft.note, facts);
  const allow = new Set(candidates.map((candidate) => candidate.id));
  const suggestionIds = [...draft.suggestionIds];
  if (new Set(suggestionIds).size !== suggestionIds.length) throw new UnsafeProviderOutput("duplicate suggestion");
  if (suggestionIds.some((id) => !allow.has(id))) throw new UnsafeProviderOutput("unapproved suggestion id");
  if (suggestionIds.length > MAX_ACTIONS[facts.surface]) throw new UnsafeProviderOutput("action count");
  const factIds = new Set(facts.statements.map((item) => item.id));
  const usedFactIds = [...new Set(draft.usedFactIds)];
  if (usedFactIds.some((id) => !factIds.has(id))) throw new UnsafeProviderOutput("unknown fact id");
  return { note, suggestionIds, usedFactIds };
}

/* ======================= the legacy (v1) gate, kept for the frozen reference contexts ======================= */

const SPACETIME_FORBIDDEN = /\b(?:influenc\w*|diffus\w*|spread\w*|migrat\w*|caus\w*|because|led to|leads? to|result(?:ed|s)? (?:in|from)|reflect\w*|important|importance|significan\w*|growth|grew|expand\w*|boom\w*|declin\w*|activity|activities|shift\w*|centre of|center of|hub|flourish\w*|dominat\w*|emerg\w*|likely|probab\w*|suggests? that|may (?:have|reflect)|colonial\w*|war|postwar|economic|political|cultural|movement of|travel\w*|nationalit\w*|birthplace|born)\b/i;
function assertLegacyNote(note: string, request: SystemSuggestionsRequest): void {
  const sentences = sentencesOf(note);
  const spacetime = request.surface === "TRACE_SPACETIME";
  const narration = isExplorationNarration(request);
  const maxSentences = spacetime ? SPACETIME_GUIDANCE_MAX_SENTENCES : narration ? EXPLORATION_NARRATION_MAX_SENTENCES : 2;
  const maxWords = spacetime ? SPACETIME_GUIDANCE_MAX_WORDS : narration ? EXPLORATION_NARRATION_MAX_WORDS : 60;
  if (sentences.length < 1 || sentences.length > maxSentences) throw new UnsafeProviderOutput("sentence count");
  if (note.split(/\s+/).filter(Boolean).length > maxWords) throw new UnsafeProviderOutput("word count");
  if (spacetime && (SPACETIME_FORBIDDEN.test(note) || /%/.test(note))) throw new UnsafeProviderOutput("spacetime forbidden claim");
}

async function legacyResponse(request: SystemSuggestionsRequest, providerStatus: string): Promise<SystemSuggestionsResponse> {
  const context = request.context as TraceSuggestionContext;
  const candidates = request.surface === "SEARCH_RESULTS" ? [] : legacyTraceCandidates(request.surface, context);
  const limit = request.surface === "TRACE_SPACETIME" ? SPACETIME_GUIDANCE_MAX_ACTIONS : isExplorationNarration(request) ? EXPLORATION_NARRATION_MAX_ACTIONS : MAX_ACTIONS[request.surface];
  let note = legacyFallbackNote(request);
  try { assertLegacyNote(note, request); } catch { note = "Guidance is unavailable for this state."; }
  return {
    schemaVersion: "gda-system-suggestions-response/v1",
    surface: request.surface,
    stateHash: request.stateHash,
    note,
    suggestions: candidates.slice(0, limit),
    sourceClass: "STATIC_FALLBACK",
    promptVersion: SYSTEM_SUGGESTIONS_PROMPT_VERSION,
    providerStatus,
  };
}

/* ======================= the v2 path ======================= */

function responseFrom(facts: SurfaceFacts, draft: ProviderDraft, candidates: readonly ApprovedSuggestion[], sourceClass: SystemSuggestionsResponse["sourceClass"], providerStatus: string, stateHash: string): SystemSuggestionsResponse {
  const byId = new Map(candidates.map((candidate) => [candidate.id, candidate]));
  return {
    schemaVersion: "gda-system-suggestions-response/v1",
    surface: facts.surface,
    stateHash,
    note: draft.note,
    suggestions: draft.suggestionIds.map((id) => byId.get(id)).filter((candidate): candidate is ApprovedSuggestion => Boolean(candidate)),
    sourceClass,
    promptVersion: SYSTEM_SUGGESTIONS_PROMPT_VERSION,
    providerStatus,
    contextFingerprint: facts.contextFingerprint,
    usedFactIds: draft.usedFactIds,
  };
}

async function fallback(facts: SurfaceFacts, candidates: readonly ApprovedSuggestion[], providerStatus: string, stateHash: string): Promise<SystemSuggestionsResponse> {
  const generated = await new StaticFallbackProvider().generate({ facts, candidates });
  try {
    return responseFrom(facts, safeDraft(generated, facts, candidates), candidates, "STATIC_FALLBACK", providerStatus, stateHash);
  } catch (error) {
    if (!(error instanceof UnsafeProviderOutput)) throw error;
    /* the deterministic note itself failed its gate: fail softly, never loudly */
    return responseFrom(facts, { note: "Guidance is unavailable for this state.", suggestionIds: [], usedFactIds: [] }, candidates, "STATIC_FALLBACK", providerStatus, stateHash);
  }
}

export async function createSystemSuggestions(rawRequest: unknown, dependencies: ServiceDependencies = {}): Promise<SystemSuggestionsResponse> {
  const parsed: SystemSuggestionsInput = parseSystemSuggestionsRequest(rawRequest);
  let request: SystemSuggestionsRequestV2;
  let stateHashEcho: string | null = null;
  if (parsed.schemaVersion === "gda-system-suggestions-request/v1") {
    /* a v1 TRACE context describes itself: it is answered deterministically and never sent to a model */
    if (parsed.surface !== "SEARCH_RESULTS") return legacyResponse(parsed, "LEGACY_CONTEXT_STATIC");
    request = { schemaVersion: "gda-system-suggestions-request/v2", surface: "SEARCH_RESULTS", reference: verifiedSearchReference(parsed) };
    stateHashEcho = parsed.stateHash;
  } else request = parsed;
  const facts = buildSurfaceFacts(request);
  const stateHash = stateHashEcho ?? facts.stateHash;
  const candidates = approvedCandidatesFromFacts(facts);
  const environment = dependencies.environment ?? process.env;
  const config = environmentConfig(environment, dependencies.timeoutMsForTest);
  const now = dependencies.now ?? Date.now;
  const key = guidanceCacheKey({ surface: facts.surface, releaseVersion: facts.releaseVersion, contextFingerprint: facts.contextFingerprint, promptVersion: SYSTEM_SUGGESTIONS_PROMPT_VERSION, language: SYSTEM_SUGGESTIONS_LANGUAGE, modelConfigVersion: modelConfigVersion(config) });
  if (config.mode === "static" || config.mode === "off") return fallback(facts, candidates, "PROVIDER_DISABLED", stateHash);
  if (!config.apiKey) return fallback(facts, candidates, "NO_KEY", stateHash);
  const cached = readGuidanceCache(key, now());
  if (cached) return { ...cached, stateHash, providerStatus: `${cached.providerStatus}_CACHED` };
  return mergeInFlight(key, async () => {
    const provider = new DeepSeekGuidanceProvider({ apiKey: config.apiKey, baseUrl: config.baseUrl, model: config.model, timeoutMs: config.timeoutMs, temperature: config.temperature, fetchImpl: dependencies.fetchImpl ?? fetch });
    try {
      const draft = safeDraft(await provider.generate({ facts, candidates }), facts, candidates);
      const response = responseFrom(facts, draft, candidates, "MODEL", "MODEL_OK", stateHash);
      storeGuidance(key, response, facts.cacheTtlMs, now());
      return response;
    } catch (error) {
      const status = error instanceof UnsafeProviderOutput ? "INVALID_RESPONSE" : error instanceof ProviderFailure ? error.status : "PROVIDER_ERROR";
      /* the same facts' verified note, if one stood before; else the deterministic note */
      const lastGood = readLastGoodGuidance(key, now());
      if (lastGood) return { ...lastGood, stateHash, providerStatus: `LAST_GOOD_AFTER_${status}` };
      return fallback(facts, candidates, status, stateHash);
    }
  });
}

/* for the verification suite: the facts and candidates a request resolves to */
export function resolveSystemSuggestionsFactsForTest(rawRequest: unknown): { facts: SurfaceFacts; candidates: ApprovedSuggestion[] } {
  const parsed = parseSystemSuggestionsRequest(rawRequest);
  if (parsed.schemaVersion !== "gda-system-suggestions-request/v2") throw new Error("v2 only");
  const facts = buildSurfaceFacts(parsed);
  return { facts, candidates: approvedCandidatesFromFacts(facts) };
}
