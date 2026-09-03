/* Pure helper — splits a paragraph into plain-text and marked-phrase segments
   for the Identity scroll interaction (HOMEPAGE_DESIGN_v1.md §3). Each mark's
   `text` must be an exact, non-overlapping substring of `source`, in order;
   marks that no longer match (copy drift) are skipped defensively rather than
   throwing, so a future copy edit degrades to "no mark" instead of a crash. */

export type IdentityMark = { id: string; text: string; mark: "underline" | "circle" };

export type IdentitySegment =
  | { kind: "text"; text: string }
  | { kind: "mark"; id: string; text: string; mark: "underline" | "circle" };

export function splitIdentityText(source: string, marks: IdentityMark[]): IdentitySegment[] {
  const segments: IdentitySegment[] = [];
  let cursor = 0;

  for (const m of marks) {
    const idx = source.indexOf(m.text, cursor);
    if (idx === -1) continue;
    if (idx > cursor) segments.push({ kind: "text", text: source.slice(cursor, idx) });
    segments.push({ kind: "mark", id: m.id, text: m.text, mark: m.mark });
    cursor = idx + m.text.length;
  }
  if (cursor < source.length) segments.push({ kind: "text", text: source.slice(cursor) });

  return segments;
}
