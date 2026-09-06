import { createHash } from "node:crypto";
import data from "../../../generated/search-unicode16/properties.json";

// Preserve the released Unicode 16 search semantics as hosts update ICU.
// Property sets and the existing lowercase+ss+sigma fold are frozen, not
// replaced with the host's newer definitions. Unassigned-16 code points are
// normalization boundaries: new host characters must not acquire meanings.
// Assigned-character normalization follows Unicode's normalization stability policy.
export const SEARCH_UNICODE_VERSION = "16.0";
const checksum = "f3b65a905b6bf9e46d6941c47dbc7883f8ab52e604c1b9b7d47f4719349e2f58";
const validData = data.unicode === SEARCH_UNICODE_VERSION && createHash("sha256").update(JSON.stringify(data) + "\n").digest("hex") === checksum;
export function supportsSearchUnicode16(): boolean {
  return validData && ["16.0", "17.0"].includes(process.versions.unicode ?? "");
}
function inRanges(character: string, ranges: readonly (readonly number[])[]): boolean {
  const cp = character.codePointAt(0)!;
  let lo = 0, hi = ranges.length - 1;
  while (lo <= hi) { const mid = (lo + hi) >>> 1, [start, end] = ranges[mid]; if (cp < start) hi = mid - 1; else if (cp > end) lo = mid + 1; else return true; }
  return false;
}
export const isMark16 = (character: string) => inRanges(character, data.ranges.mark);
export const isLatin16 = (character: string) => inRanges(character, data.ranges.latin);
export const isNumber16 = (character: string) => inRanges(character, data.ranges.number);
export const isLatinOrNumber16 = (character: string) => isLatin16(character) || isNumber16(character);
export const isSeparator16 = (character: string) => inRanges(character, data.ranges.separator);
export function caseFold16(value: string): string {
  const map = data.lower as Record<string, string>;
  return Array.from(value, c => map[String(c.codePointAt(0))] ?? c).join("");
}
export function normalize16(value: string, form: "NFC" | "NFD" | "NFKC" = "NFC"): string {
  let run = "", output = "";
  for (const c of value) {
    if (inRanges(c, data.ranges.assigned)) run += c;
    else { output += run.normalize(form) + c; run = ""; }
  }
  return output + run.normalize(form);
}
