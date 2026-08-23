export const CONTEXT_CANVAS_DISPLAY_LABEL_POLICY_VERSION = 1 as const;
export const CONTEXT_CANVAS_NODE_LABEL_DISPLAY_UNIT_LIMIT = 18;
export const CONTEXT_CANVAS_NODE_ID_DISPLAY_UNIT_LIMIT = 22;
export const CONTEXT_CANVAS_CONNECTION_LABEL_DISPLAY_UNIT_LIMIT = 30;

export interface ContextCanvasDisplayLabel {
  readonly fullText: string;
  readonly displayText: string;
  readonly graphemeCount: number;
  readonly displayUnitCount: number;
  readonly truncated: boolean;
}

const segmenter = typeof Intl.Segmenter === "function"
  ? new Intl.Segmenter("und", { granularity: "grapheme" })
  : null;

const DISPLAY_CONTROL_CHARACTERS = /[\u0000-\u001f\u007f-\u009f]/gu;
const DISPLAY_WHITESPACE = /\s+/gu;

function replaceLoneSurrogates(value: string): string {
  let result = "";
  for (let index = 0; index < value.length; index += 1) {
    const codeUnit = value.charCodeAt(index);
    if (codeUnit >= 0xd800 && codeUnit <= 0xdbff) {
      const nextCodeUnit = value.charCodeAt(index + 1);
      if (nextCodeUnit >= 0xdc00 && nextCodeUnit <= 0xdfff) {
        result += value[index] + value[index + 1];
        index += 1;
      } else {
        result += "\ufffd";
      }
    } else if (codeUnit >= 0xdc00 && codeUnit <= 0xdfff) {
      result += "\ufffd";
    } else {
      result += value[index];
    }
  }
  return result;
}

function graphemes(value: string): readonly string[] {
  if (!segmenter) return Array.from(value);
  return Array.from(segmenter.segment(value), (part) => part.segment);
}

function displayCandidate(value: string): string {
  return replaceLoneSurrogates(value)
    .replace(DISPLAY_CONTROL_CHARACTERS, " ")
    .replace(DISPLAY_WHITESPACE, " ")
    .trim();
}

function graphemeDisplayUnits(value: string): number {
  const codePoint = value.codePointAt(0) ?? 0;
  const wideUnicode = codePoint >= 0x1100 && (
    codePoint <= 0x115f
    || codePoint === 0x2329
    || codePoint === 0x232a
    || (codePoint >= 0x2e80 && codePoint <= 0xa4cf && codePoint !== 0x303f)
    || (codePoint >= 0xac00 && codePoint <= 0xd7a3)
    || (codePoint >= 0xf900 && codePoint <= 0xfaff)
    || (codePoint >= 0xfe10 && codePoint <= 0xfe19)
    || (codePoint >= 0xfe30 && codePoint <= 0xfe6f)
    || (codePoint >= 0xff00 && codePoint <= 0xff60)
    || (codePoint >= 0xffe0 && codePoint <= 0xffe6)
    || (codePoint >= 0x1f000 && codePoint <= 0x1faff)
    || (codePoint >= 0x20000 && codePoint <= 0x3fffd)
  );
  const conservativelyWideLatin = /^[A-Zmw@#%&]$/u.test(value);
  return wideUnicode || conservativelyWideLatin || codePoint > 0x7f ? 2 : 1;
}

export function contextCanvasFullLabel(
  value: Readonly<{ stableId: string; label?: string }>,
): string {
  return value.label && value.label.trim() ? value.label : value.stableId;
}

export function fitContextCanvasDisplayLabel(
  value: string,
  maxDisplayUnits = CONTEXT_CANVAS_NODE_LABEL_DISPLAY_UNIT_LIMIT,
): ContextCanvasDisplayLabel {
  const limit = Number.isSafeInteger(maxDisplayUnits) ? Math.max(2, maxDisplayUnits) : 2;
  const candidate = displayCandidate(value) || "Untitled";
  const segments = graphemes(candidate);
  const displayUnitCount = segments.reduce((count, segment) => count + graphemeDisplayUnits(segment), 0);
  const truncated = displayUnitCount > limit;
  const kept: string[] = [];
  let keptUnits = 0;
  if (truncated) {
    for (const segment of segments) {
      const nextUnits = graphemeDisplayUnits(segment);
      const ellipsisUnits = 2;
      if (keptUnits + nextUnits + ellipsisUnits > limit) break;
      kept.push(segment);
      keptUnits += nextUnits;
    }
  }
  return Object.freeze({
    fullText: value,
    displayText: truncated ? `${kept.join("")}…` : candidate,
    graphemeCount: segments.length,
    displayUnitCount,
    truncated,
  });
}

function isXml10CodePoint(codePoint: number): boolean {
  if (codePoint === 0x9 || codePoint === 0xa || codePoint === 0xd) return true;
  if (codePoint >= 0x20 && codePoint <= 0xd7ff) return true;
  if (codePoint >= 0xe000 && codePoint <= 0xfffd) {
    return codePoint !== 0xfffe && codePoint !== 0xffff;
  }
  return codePoint >= 0x10000
    && codePoint <= 0x10ffff
    && (codePoint & 0xffff) !== 0xfffe
    && (codePoint & 0xffff) !== 0xffff;
}

export function escapeContextCanvasXml(value: string): string {
  let escaped = "";
  for (const character of value) {
    const codePoint = character.codePointAt(0) ?? 0xfffd;
    if (!isXml10CodePoint(codePoint)) {
      escaped += "&#xFFFD;";
    } else if (codePoint >= 0x7f && codePoint <= 0x9f) {
      escaped += `&#x${codePoint.toString(16).toUpperCase()};`;
    } else if (character === "&") escaped += "&amp;";
    else if (character === "<") escaped += "&lt;";
    else if (character === ">") escaped += "&gt;";
    else if (character === '"') escaped += "&quot;";
    else if (character === "'") escaped += "&apos;";
    else escaped += character;
  }
  return escaped;
}
