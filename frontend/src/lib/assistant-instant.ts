import type {
  AssistantCandidateEvidence,
  AssistantEvidence,
} from "@/lib/assistant-retrieval";

export interface InstantAssistantContext {
  surfaceId?: string;
  title?: string;
  dateText?: string;
  imageState?: string;
  rightsLabel?: string;
  sourceName?: string;
  creator?: string;
  objectType?: string;
}

type InstantIntent =
  | "rights"
  | "source"
  | "recommendation"
  | "current"
  | "next"
  | "fallback";

const IMAGE_POLICY: Record<string, string> = {
  IMG00: "no image bay; use metadata and source evidence only",
  IMG01: "thumbnail-visible evidence, not an automatic open-image claim",
  IMG02: "source-viewer evidence; keep the image source-linked",
  IMG03: "verified open-image frame when the source and rights evidence support it",
  IMG04: "text-only signal; useful for source context but weak for an image-based archive",
};

export const INSTANT_ASSISTANT_RESPONSE_SCRIPTS = [
  {
    intent: "current",
    user: "what could you tell about this work?",
    assistant:
      "This page is best read as a source-linked object record: title, date, image state, and source are already enough to orient the work. I would use it as a starting point, then open the source before making any stronger historical claim.",
  },
  {
    intent: "recommendation",
    user: "what is the most impressive piece in 1970s france?",
    assistant:
      "In the current archive, I would start with the highest-ranked candidate rather than call it an objective canon. The ranking is based on date, region, image state, source visibility, and graphic-design signals.",
  },
  {
    intent: "rights",
    user: "can this image be used?",
    assistant:
      "Treat the image state as display evidence, not a permission shortcut. IMG03 can support open-image use; IMG01 and IMG02 need source-linked handling unless a stricter rights review upgrades them.",
  },
  {
    intent: "source",
    user: "where is this from?",
    assistant:
      "Use the source name and source URL as the first citation layer. The archive note can guide reading, but the source page remains the authority for object metadata and rights evidence.",
  },
];

function normalize(value: string) {
  return value.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
}

function detectIntent(question: string): InstantIntent {
  const q = normalize(question);
  if (
    /\b(rights?|license|copyright|open|image|img0[0-4]|download|copy|use)\b/.test(q)
  ) {
    return "rights";
  }
  if (/\b(source|citation|cite|link|metadata|where from|from)\b/.test(q)) {
    return "source";
  }
  if (
    /\b(best|most|strongest|impressive|important|recommend|pick|should check)\b/.test(
      q,
    )
  ) {
    return "recommendation";
  }
  if (/\b(next|compare|relation|related|look at|check next)\b/.test(q)) {
    return "next";
  }
  if (/\b(this|work|object|tell|about|explain|what is)\b/.test(q)) {
    return "current";
  }
  return "fallback";
}

function compactContext(context?: InstantAssistantContext | null) {
  if (!context) return "";
  return [
    context.title,
    context.dateText,
    context.creator,
    context.objectType,
    context.sourceName,
  ]
    .filter(Boolean)
    .join(", ");
}

function sourceLabel(candidate?: AssistantCandidateEvidence) {
  if (!candidate) return "";
  return candidate.sourceUrl
    ? `${candidate.sourceName} (${candidate.sourceUrl})`
    : candidate.sourceName;
}

function candidateLine(candidate: AssistantCandidateEvidence) {
  const creator =
    candidate.creator && candidate.creator !== "unknown"
      ? `; ${candidate.creator}`
      : "";
  return `${candidate.title} (${candidate.dateText}${creator}; ${candidate.surfaceId})`;
}

function topCandidate(evidence: AssistantEvidence) {
  return evidence.candidates[0];
}

function readingAngle(
  context?: InstantAssistantContext | null,
  candidate?: AssistantCandidateEvidence,
) {
  const imageState = context?.imageState ?? candidate?.imageState ?? "unknown";
  const objectType = context?.objectType ?? candidate?.objectType ?? "object record";
  const sourceName = context?.sourceName ?? candidate?.sourceName ?? "source record";
  return `Reading angle: treat it as ${objectType} evidence anchored by ${sourceName}; image state ${imageState} controls how far the visual claim can go.`;
}

function rightsAnswer(
  context: InstantAssistantContext | null | undefined,
  evidence: AssistantEvidence,
) {
  const candidate = topCandidate(evidence);
  const imageState = context?.imageState ?? candidate?.imageState ?? "unknown";
  const rights = context?.rightsLabel || "rights evidence not fully stated here";
  const policy = IMAGE_POLICY[imageState] ?? "review the source before claiming display rights";
  return `Image state is ${imageState}: ${policy}. Rights note: ${rights}. I would keep this source-linked unless the record is clearly IMG03 with source-side open evidence.`;
}

function sourceAnswer(
  context: InstantAssistantContext | null | undefined,
  evidence: AssistantEvidence,
) {
  const candidate = topCandidate(evidence);
  const source =
    context?.sourceName ||
    sourceLabel(candidate) ||
    "the current source record in the archive payload";
  const title = context?.title || candidate?.title || "this record";
  return `${title} is currently anchored to ${source}. Use that source page as the citation authority; the assistant can summarize the archive record, but it should not replace source verification.`;
}

function recommendationAnswer(evidence: AssistantEvidence) {
  const [first, second] = evidence.candidates;
  if (!first) {
    return evidence.fallbackAnswer ?? "I do not have enough archive evidence to rank this.";
  }
  const next = second ? ` A second check would be ${candidateLine(second)}.` : "";
  return `In the current archive, I would start with ${candidateLine(first)}. This is an archive-navigation pick based on date/region fit, image state, source visibility, and design-signal ranking, not an objective canon.${next}`;
}

function currentAnswer(
  context: InstantAssistantContext | null | undefined,
  evidence: AssistantEvidence,
) {
  const candidate = topCandidate(evidence);
  const title = context?.title || candidate?.title || "this record";
  const date = context?.dateText || candidate?.dateText || "undated";
  const source = context?.sourceName || candidate?.sourceName || "source record";
  const summary = compactContext(context) || candidate?.note || title;
  return `${title} is indexed here as a source-linked archive record, dated ${date}, with source evidence from ${source}. ${readingAngle(context, candidate)} Current context: ${summary}.`;
}

function nextAnswer(evidence: AssistantEvidence) {
  const candidates = evidence.candidates.slice(0, 3);
  if (candidates.length === 0) {
    return evidence.fallbackAnswer ?? "I do not have enough archive evidence to suggest a next check.";
  }
  return `Next, I would compare ${candidates.map(candidateLine).join("; ")}. That keeps the reading grounded in retrieved archive records instead of drifting into general design-history claims.`;
}

export function buildInstantAssistantAnswer({
  question,
  context,
  evidence,
}: {
  question: string;
  context?: InstantAssistantContext | null;
  evidence: AssistantEvidence;
}) {
  if (!evidence.hasEvidence && !context?.title) {
    return (
      evidence.fallbackAnswer ??
      "I do not have enough archive evidence to answer that without inventing."
    );
  }

  const intent = detectIntent(question);
  if (intent === "rights") return rightsAnswer(context, evidence);
  if (intent === "source") return sourceAnswer(context, evidence);
  if (intent === "recommendation") return recommendationAnswer(evidence);
  if (intent === "next") return nextAnswer(evidence);
  if (intent === "current") return currentAnswer(context, evidence);
  return currentAnswer(context, evidence);
}
