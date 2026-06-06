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
  fallbackAnswer?: string;
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

export function buildAssistantEvidence(
  question: string,
  context?: AssistantRetrievalContext | null,
  options?: { research?: boolean },
): AssistantEvidence {
  const terms = queryTerms(question);
  const dateWindow = parseDateWindow(question);
  const regionFolder = regionFoldersFromText(question, context)[0] ?? null;
  const activeSurface = context?.surfaceId ? getSurface(context.surfaceId) : undefined;

  let pool = getSurfaces();
  if (dateWindow) {
    pool = pool.filter((surface) => surfaceOverlapsDate(surface, dateWindow));
  }
  if (regionFolder) {
    pool = pool.filter((surface) => surfaceInFolder(surface, regionFolder));
  }

  if (pool.length === 0) {
    const fuzzy = fuzzySearchSurfaces(question).map((result) => result.surface);
    pool = [...fuzzy];
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

  const limit = options?.research ? 10 : 3;
  const snippetLength = options?.research ? 220 : 120;
  const selected = candidates.slice(0, limit);

  if (selected.length === 0) {
    return {
      hasEvidence: false,
      candidateCount: 0,
      contextText: "",
      candidates: [],
      fallbackAnswer:
        "I do not have enough matching archive evidence in the current payload to answer that without inventing. Try a region, decade, title, creator, source, or medium from the archive index.",
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
    : "Answer from the retrieved candidates and cite surface IDs.";

  return {
    hasEvidence: true,
    candidateCount: candidates.length,
    candidates: selected.map((candidate) =>
      toCandidateEvidence(candidate, snippetLength),
    ),
    contextText: [
      "ARCHIVE_RETRIEVAL_CONTEXT",
      parseLine,
      guidance,
      "Do not mention records not present in these candidates.",
      "Discussing metadata, source evidence, rights state, and archive navigation is allowed; do not refuse as copyright infringement unless the user asks to copy, download, or bypass rights.",
      "CANDIDATES",
      selected
        .map((candidate, index) => formatCandidate(candidate, index, snippetLength))
        .join("\n---\n"),
    ].join("\n"),
  };
}
