import {
  fuzzySearchSurfaces,
  getFolders,
  getSurface,
  getSurfaces,
} from "@/lib/archive-data";
import type { Folder, Surface } from "@/types/archive";

export interface AssistantRetrievalContext {
  surfaceId?: string;
  title?: string;
  dateText?: string;
  sourceName?: string;
}

export interface AssistantEvidence {
  hasEvidence: boolean;
  candidateCount: number;
  contextText: string;
  candidates: AssistantCandidateEvidence[];
  requestPlan: AssistantRequestPlan;
  fallbackAnswer?: string;
}

export type AssistantRequestIntent =
  | "archive_intro"
  | "earliest_candidate"
  | "recommendation"
  | "current_object"
  | "rights_image"
  | "comparison"
  | "source_lookup"
  | "open_exploration";

export interface AssistantRequestPlan {
  intent: AssistantRequestIntent;
  answerJob: string;
  answerShape: string;
  evidencePolicy: string;
  focusTerms: string[];
}

export interface AssistantCandidateEvidence {
  surfaceId: string;
  title: string;
  dateText: string;
  creator: string;
  placeText: string;
  objectType: string;
  imageState: string;
  sourceName: string;
  sourceUrl: string;
  score: number;
  reasons: string[];
  note: string;
}

interface DateWindow {
  label: string;
  start: number;
  end: number;
}

interface Candidate {
  surface: Surface;
  score: number;
  reasons: string[];
}

const STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "any",
  "are",
  "best",
  "check",
  "could",
  "for",
  "from",
  "i",
  "in",
  "is",
  "me",
  "most",
  "of",
  "on",
  "piece",
  "should",
  "tell",
  "the",
  "this",
  "to",
  "what",
  "which",
  "work",
  "you",
]);

function normalize(value: string) {
  return value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
}

function queryTerms(question: string) {
  return normalize(question)
    .split(/\s+/)
    .filter((term) => term.length >= 3 && !STOPWORDS.has(term));
}

function includesAny(value: string, patterns: RegExp[]) {
  return patterns.some((pattern) => pattern.test(value));
}

function parseDateWindow(question: string): DateWindow | null {
  const q = question.toLowerCase();
  const decade = q.match(/\b((?:18|19|20)\d0)s\b/);
  if (decade) {
    const start = Number(decade[1]);
    return { label: `${start}s`, start, end: start + 9 };
  }
  const year = q.match(/\b((?:18|19|20)\d{2})\b/);
  if (year) {
    const value = Number(year[1]);
    return { label: String(value), start: value, end: value };
  }
  return null;
}

function surfaceOverlapsDate(surface: Surface, window: DateWindow) {
  const start = surface.dateStart ?? surface.dateEnd;
  const end = surface.dateEnd ?? surface.dateStart;
  if (start === null || start === undefined || end === null || end === undefined) {
    return false;
  }
  return start <= window.end && end >= window.start;
}

function regionFoldersFromText(question: string, context?: AssistantRetrievalContext | null) {
  const q = normalize([question, context?.title, context?.sourceName].filter(Boolean).join(" "));
  const regions = getFolders().filter((folder) => folder.type === "region");
  return regions
    .filter((folder) => {
      const title = normalize(folder.title);
      const slug = normalize(folder.slug.replace(/-/g, " "));
      return q.includes(title) || q.includes(slug);
    })
    .sort((a, b) => b.title.length - a.title.length);
}

function surfaceInFolder(surface: Surface, folder: Folder) {
  return surface.folders.some((item) => item.folderId === folder.folderId);
}

function sourceText(surface: Surface) {
  return [
    surface.title,
    surface.creator,
    surface.placeText,
    surface.objectType,
    surface.medium,
    surface.sourceName,
    surface.descriptionSummary,
    surface.sourceDescription,
    surface.historicalContextNote,
    surface.classificationRationale,
    surface.citationBasis,
  ]
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

function snippet(surface: Surface, length = 220) {
  return sourceText(surface).slice(0, length);
}

function imageScore(surface: Surface) {
  if (surface.image.state === "IMG03") return 22;
  if (surface.image.state === "IMG02") return 16;
  if (surface.image.state === "IMG01") return 14;
  if (surface.image.state === "IMG04") return 3;
  return 0;
}

function designSignalScore(surface: Surface) {
  const text = normalize(
    [surface.title, surface.objectType, surface.medium, surface.sourceSubjects]
      .filter(Boolean)
      .join(" "),
  );
  let score = 0;
  if (text.includes("poster")) score += 18;
  if (text.includes("typograph") || text.includes("typographie")) score += 14;
  if (text.includes("publicit") || text.includes("advertis")) score += 14;
  if (text.includes("graphic")) score += 10;
  if (text.includes("stamp")) score -= 6;
  return score;
}

function rankCandidate(
  surface: Surface,
  terms: string[],
  dateWindow: DateWindow | null,
  regionFolder: Folder | null,
): Candidate {
  const reasons: string[] = [];
  let score = 0;

  if (dateWindow && surfaceOverlapsDate(surface, dateWindow)) {
    score += 100;
    reasons.push(`date matches ${dateWindow.label}`);
  }
  if (regionFolder && surfaceInFolder(surface, regionFolder)) {
    score += 100;
    reasons.push(`region folder matches ${regionFolder.title}`);
  }

  score += imageScore(surface);
  if (["IMG01", "IMG02", "IMG03"].includes(surface.image.state)) {
    reasons.push(`image state ${surface.image.state}`);
  }

  const designScore = designSignalScore(surface);
  if (designScore > 0) reasons.push("graphic-design signal");
  score += designScore;

  if (surface.sourceUrl) score += 8;
  score += Math.min(20, Math.max(0, surface.completenessScore ?? 0) / 5);
  score += Math.min(12, Math.floor((surface.readingTextLength ?? 0) / 600));

  const haystack = normalize(sourceText(surface));
  for (const term of terms) {
    if (haystack.includes(term)) score += 8;
  }

  return { surface, score, reasons };
}

function formatCandidate(candidate: Candidate, index: number, snippetLength = 220) {
  const { surface, score, reasons } = candidate;
  return [
    `${index + 1}. ${surface.surfaceId} | ${surface.title}`,
    `   date=${surface.dateText || surface.dateStart || "unknown"}; creator=${surface.creator || "unknown"}; place=${surface.placeText || "unknown"}`,
    `   object=${surface.objectType || surface.medium || "unknown"}; image=${surface.image.state}; source=${surface.sourceName || "unknown"}`,
    `   source_url=${surface.sourceUrl || "none"}`,
    `   ranking_score=${score.toFixed(1)}; reasons=${reasons.join(", ") || "metadata overlap"}`,
    `   note=${snippet(surface, snippetLength) || "no note available"}`,
  ].join("\n");
}

function superlativeQuestion(question: string) {
  return /\b(best|most|strongest|impressive|important|recommend|check)\b/i.test(question);
}

function firstOrEarliestQuestion(question: string) {
  return /\b(first|earliest|oldest|initial|when did|when is|when was)\b/i.test(
    question,
  );
}

function focusTerms(question: string, terms: string[]) {
  const normalized = normalize(question);
  const detected = new Set<string>();
  const focusPatterns: [string, RegExp][] = [
    ["advertising", /\b(advertis\w*|publicit\w*|commercial)\b/i],
    ["poster", /\bposter\w*\b/i],
    ["typography", /\b(type|typograph\w*|letterform|font)\b/i],
    ["studio", /\b(studio|agency|collective)\b/i],
    ["platform", /\b(platform|website|digital|internet|online)\b/i],
    ["stamp", /\b(stamp|philatel\w*)\b/i],
    ["visual communication", /\b(visual communication|graphic design|graphic art)\b/i],
    ["rights", /\b(rights?|license|licence|copyright|open|public domain|img0[1-4])\b/i],
  ];

  for (const [label, pattern] of focusPatterns) {
    if (pattern.test(question)) detected.add(label);
  }
  for (const term of terms) {
    if (normalized.includes(term)) detected.add(term);
  }
  return Array.from(detected).slice(0, 8);
}

function requestIntent(question: string, context?: AssistantRetrievalContext | null) {
  const q = question.toLowerCase();
  if (
    includesAny(q, [
      /\b(what are you|who are you|introduce|about this archive|how do i use|what is this archive)\b/,
      /\barchive\b.*\b(about|for|do|use)\b/,
    ])
  ) {
    return "archive_intro" as const;
  }
  if (
    includesAny(q, [
      /\b(rights?|license|licence|copyright|open|public domain|img0[1-4])\b/,
    ])
  ) {
    return "rights_image" as const;
  }
  if (firstOrEarliestQuestion(question)) return "earliest_candidate" as const;
  if (superlativeQuestion(question)) return "recommendation" as const;
  if (includesAny(q, [/\b(compare|versus|vs\.?|difference|between)\b/])) {
    return "comparison" as const;
  }
  if (includesAny(q, [/\b(source|citation|provenance|where from|archive record)\b/])) {
    return "source_lookup" as const;
  }
  if (context?.surfaceId && includesAny(q, [/\b(this|current|object|work|piece)\b/])) {
    return "current_object" as const;
  }
  return "open_exploration" as const;
}

function buildRequestPlan({
  question,
  terms,
  dateWindow,
  regionFolder,
  context,
  candidateCount,
  hasCandidates,
  research,
}: {
  question: string;
  terms: string[];
  dateWindow: DateWindow | null;
  regionFolder: Folder | null;
  context?: AssistantRetrievalContext | null;
  candidateCount: number;
  hasCandidates: boolean;
  research?: boolean;
}): AssistantRequestPlan {
  const intent = requestIntent(question, context);
  const focus = focusTerms(question, terms);
  const scope = [
    regionFolder ? `region=${regionFolder.title}` : null,
    dateWindow ? `date=${dateWindow.label}` : null,
    focus.length ? `focus=${focus.join(", ")}` : null,
  ]
    .filter(Boolean)
    .join("; ");

  if (intent === "archive_intro") {
    return {
      intent,
      focusTerms: focus,
      answerJob:
        "Introduce the archive as a rights-aware graphic design history index and suggest one practical way to explore it.",
      answerShape: research
        ? "Three compact parts: what it is, how to read a surface, what to check next."
        : "One warm, practical sentence.",
      evidencePolicy:
        "General archive orientation is allowed; do not pretend a candidate list is required.",
    };
  }

  if (intent === "earliest_candidate") {
    return {
      intent,
      focusTerms: focus,
      answerJob: `Find the earliest or first plausible archive candidate${scope ? ` within ${scope}` : ""}.`,
      answerShape:
        "Name one candidate if evidence supports it; otherwise say the archive does not prove a first record and suggest a sharper search route.",
      evidencePolicy:
        "Do not make an objective historical first claim. Treat the result as current-archive evidence only.",
    };
  }

  if (intent === "recommendation") {
    return {
      intent,
      focusTerms: focus,
      answerJob: `Recommend the strongest current archive candidate${scope ? ` within ${scope}` : ""}.`,
      answerShape:
        "Give one pick, one reason, and one caveat or next check. Avoid list-like catalog prose.",
      evidencePolicy:
        "Use ranking as a navigation aid only; do not turn it into canon or impact proof.",
    };
  }

  if (intent === "rights_image") {
    return {
      intent,
      focusTerms: focus,
      answerJob: "Explain what the current evidence can say about image state, rights state, or source visibility.",
      answerShape:
        "Be direct about the IMG state and the next verification step. Do not upgrade rights.",
      evidencePolicy:
        "Rights evidence is descriptive only. Never imply download permission beyond the recorded evidence.",
    };
  }

  if (intent === "comparison") {
    return {
      intent,
      focusTerms: focus,
      answerJob: "Compare the best available candidates or explain why the archive evidence is too thin for comparison.",
      answerShape:
        "Use a compact contrast, then suggest the next evidence check.",
      evidencePolicy:
        "Only compare records present in the retrieved candidates.",
    };
  }

  if (intent === "source_lookup") {
    return {
      intent,
      focusTerms: focus,
      answerJob: "Orient the user to source evidence, citation basis, and what the source can support.",
      answerShape:
        "Mention the source or surface ID only if it helps the user decide what to open next.",
      evidencePolicy:
        "Do not infer unavailable source details. Stay with the retrieved source fields.",
    };
  }

  if (intent === "current_object") {
    return {
      intent,
      focusTerms: focus,
      answerJob:
        "Help the user read the active archive object and decide what to inspect next.",
      answerShape:
        "One concise reading note plus a next check.",
      evidencePolicy:
        "Use active context first, then retrieved candidates only when they add evidence.",
    };
  }

  return {
    intent,
    focusTerms: focus,
    answerJob: hasCandidates
      ? `Answer the user's archive question from ${candidateCount} retrieved candidate(s).`
      : "Respond conversationally while making clear that the current archive payload has no matching evidence.",
    answerShape: research
      ? "Use Evidence, Reading, and Next checks."
      : "One or two compact, useful sentences.",
    evidencePolicy:
      "Do not invent records. If evidence is weak, say what query direction would improve it.",
  };
}

function requestPlanText(plan: AssistantRequestPlan) {
  return [
    `intent=${plan.intent}`,
    `answer_job=${plan.answerJob}`,
    `answer_shape=${plan.answerShape}`,
    `evidence_policy=${plan.evidencePolicy}`,
    `focus_terms=${plan.focusTerms.length ? plan.focusTerms.join(", ") : "none"}`,
    "planner_rule=Use this as routing guidance only; do not quote it as the answer.",
  ].join("\n");
}

function scopedNoEvidenceAnswer({
  requestPlan,
  dateWindow,
  regionFolder,
}: {
  requestPlan: AssistantRequestPlan;
  dateWindow: DateWindow | null;
  regionFolder: Folder | null;
}) {
  const scope = [
    regionFolder?.title,
    dateWindow?.label,
    requestPlan.focusTerms.length ? requestPlan.focusTerms.join(" / ") : null,
  ]
    .filter(Boolean)
    .join(", ");
  if (requestPlan.intent === "earliest_candidate") {
    return scope
      ? `I cannot prove a first record for ${scope} from the current archive evidence. Broaden the route by decade, medium, source family, or adjacent regional terms before treating anything as first.`
      : "I cannot prove a first record from the current archive evidence. Try adding a region, decade, medium, source, or title before treating anything as first.";
  }
  if (requestPlan.intent === "recommendation") {
    return scope
      ? `I do not see a strong current-archive candidate for ${scope}. Broaden the filter or ask for a nearby decade, medium, or source family.`
      : "I do not see a strong current-archive candidate for that yet. Add a region, decade, medium, source, or title and I can give a better pick.";
  }
  if (requestPlan.intent === "rights_image") {
    return "I do not have enough matching archive evidence to read the rights or image state safely. Open a specific surface or source record first.";
  }
  return scope
    ? `I do not have enough matching archive evidence for ${scope}. Try a broader region, decade, medium, source, or title.`
    : "I do not have enough matching archive evidence to answer that without inventing. Try a region, decade, title, creator, source, or medium from the archive index.";
}

function toCandidateEvidence(
  candidate: Candidate,
  snippetLength: number,
): AssistantCandidateEvidence {
  const { surface, score, reasons } = candidate;
  return {
    surfaceId: surface.surfaceId,
    title: surface.title,
    dateText: surface.dateText || String(surface.dateStart || "unknown"),
    creator: surface.creator || "unknown",
    placeText: surface.placeText || "unknown",
    objectType: surface.objectType || surface.medium || "unknown",
    imageState: surface.image.state,
    sourceName: surface.sourceName || "unknown",
    sourceUrl: surface.sourceUrl || "",
    score,
    reasons,
    note: snippet(surface, snippetLength),
  };
}

function termMatches(surface: Surface, terms: string[]) {
  const haystack = normalize(sourceText(surface));
  return terms.filter((term) => haystack.includes(term)).slice(0, 8);
}

function fastEvidenceText({
  requestPlan,
  candidate,
  terms,
  dateWindow,
  regionFolder,
  candidateCount,
  question,
}: {
  requestPlan: AssistantRequestPlan;
  candidate: Candidate;
  terms: string[];
  dateWindow: DateWindow | null;
  regionFolder: Folder | null;
  candidateCount: number;
  question: string;
}) {
  const { surface, score, reasons } = candidate;
  const matches = termMatches(surface, terms);
  const firstRule = firstOrEarliestQuestion(question)
    ? "If answering a first/earliest question, call this a current-archive lead, not a proven historical first."
    : null;
  const recommendRule = superlativeQuestion(question)
    ? "If answering a recommendation/superlative, give one pick and one caveat."
    : null;
  return [
    `REQUEST_PLAN intent=${requestPlan.intent}; job=${requestPlan.answerJob}; shape=one complete concise assistant sentence.`,
    `QUERY_SCOPE region=${regionFolder?.title ?? "none"}; date=${dateWindow?.label ?? "none"}; candidates=${candidateCount}.`,
    firstRule,
    recommendRule,
    "TOP_ARCHIVE_LEAD",
    `surface=${surface.surfaceId}`,
    `title=${surface.title}`,
    `date=${surface.dateText || surface.dateStart || "unknown"}`,
    `place=${surface.placeText || "unknown"}`,
    `object=${surface.objectType || surface.medium || "unknown"}`,
    `image=${surface.image.state}`,
    `source=${surface.sourceName || "unknown"}`,
    `score=${score.toFixed(1)}; reasons=${reasons.join(", ") || "metadata overlap"}; term_matches=${matches.length ? matches.join(", ") : "weak"}`,
    `note=${snippet(surface, 80) || "no note available"}`,
    "Do not list alternatives. Do not invent beyond this lead.",
  ]
    .filter(Boolean)
    .join("\n");
}

export function buildAssistantEvidence(
  question: string,
  context?: AssistantRetrievalContext | null,
  options?: { research?: boolean },
): AssistantEvidence {
  const terms = queryTerms(question);
  const dateWindow = parseDateWindow(question);
  const regionFolder = regionFoldersFromText(question, context)[0] ?? null;
  const activeSurface = context?.surfaceId ? getSurface(context.surfaceId) : undefined;
  const scopedQuery = Boolean(dateWindow || regionFolder);

  let pool = getSurfaces();
  if (dateWindow) {
    pool = pool.filter((surface) => surfaceOverlapsDate(surface, dateWindow));
  }
  if (regionFolder) {
    pool = pool.filter((surface) => surfaceInFolder(surface, regionFolder));
  }

  if (pool.length === 0) {
    pool = scopedQuery
      ? []
      : fuzzySearchSurfaces(question).map((result) => result.surface);
  }
  if (activeSurface && !pool.some((surface) => surface.surfaceId === activeSurface.surfaceId)) {
    pool.unshift(activeSurface);
  }

  const candidates = pool
    .map((surface) => rankCandidate(surface, terms, dateWindow, regionFolder))
    .filter((candidate) => candidate.score > 0)
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return (b.surface.completenessScore ?? 0) - (a.surface.completenessScore ?? 0);
    });

  const limit = options?.research ? 10 : 1;
  const snippetLength = options?.research ? 220 : 80;
  const selected = candidates.slice(0, limit);
  const requestPlan = buildRequestPlan({
    question,
    terms,
    dateWindow,
    regionFolder,
    context,
    candidateCount: candidates.length,
    hasCandidates: selected.length > 0,
    research: options?.research,
  });

  if (selected.length === 0) {
    return {
      hasEvidence: false,
      candidateCount: 0,
      contextText: [
        "REQUEST_PLAN",
        requestPlanText(requestPlan),
        "ARCHIVE_RETRIEVAL_CONTEXT",
        "candidate_count=0",
        "NO_MATCHING_CANDIDATES",
      ].join("\n"),
      candidates: [],
      requestPlan,
      fallbackAnswer: scopedNoEvidenceAnswer({
        requestPlan,
        dateWindow,
        regionFolder,
      }),
    };
  }

  const top = selected[0].surface;
  const parseLine = [
    `date_window=${dateWindow ? `${dateWindow.label} (${dateWindow.start}-${dateWindow.end})` : "not specified"}`,
    `region=${regionFolder?.title ?? "not specified"}`,
    `candidate_count=${candidates.length}`,
    `mode=${options?.research ? "research" : "assistant"}`,
  ].join("; ");

  const guidance = superlativeQuestion(question)
    ? `The user is asking for a recommendation/superlative. Treat "most impressive" as an archive-navigation judgment, not an objective historical fact. The strongest current candidate is ${top.surfaceId}: ${top.title}.`
    : firstOrEarliestQuestion(question)
    ? `The user is asking for a first/earliest answer. Use the strongest current candidate only as archive evidence, and caveat if focus terms are weak. The strongest current candidate is ${top.surfaceId}: ${top.title}.`
    : "Answer from the retrieved candidates and cite surface IDs.";

  return {
    hasEvidence: true,
    candidateCount: candidates.length,
    candidates: selected.map((candidate) =>
      toCandidateEvidence(candidate, snippetLength),
    ),
    requestPlan,
    contextText: options?.research
      ? [
          "REQUEST_PLAN",
          requestPlanText(requestPlan),
          "ARCHIVE_RETRIEVAL_CONTEXT",
          parseLine,
          guidance,
          "Do not mention records not present in these candidates.",
          "Discussing metadata, source evidence, rights state, and archive navigation is allowed; do not refuse as copyright infringement unless the user asks to copy, download, or bypass rights.",
          "CANDIDATES",
          selected
            .map((candidate, index) =>
              formatCandidate(candidate, index, snippetLength),
            )
            .join("\n---\n"),
        ].join("\n")
      : fastEvidenceText({
          requestPlan,
          candidate: selected[0],
          terms,
          dateWindow,
          regionFolder,
          candidateCount: candidates.length,
          question,
        }),
  };
}
