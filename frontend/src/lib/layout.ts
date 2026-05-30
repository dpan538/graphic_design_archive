/**
 * Layout template system.
 *
 * Nine reusable page layouts. Data is read from the static payload and dropped
 * into fixed slots — missing data leaves a reserved empty slot. The selection
 * function is deterministic so the same payload always produces the same
 * layout (reproducible, build-time / SSG friendly).
 *
 *  L01 main.standard   — the single canonical main-sheet format (+ variants)
 *  L02 text.only       — pure text/table sheet (IMG04, no image frame)
 *  L03 plate.dominant  — the one image-led format (image ≈ 60%)
 *  L04 sheet.dual      — two photos arranged on one page
 *  L05 sheet.compound  — several weak records as one intellectual unit
 *  L06 card.sparse     — sparse card with promotion/review status
 *  L07 stub.fallback   — deliberate "not ingested" stub
 *  L08 appendix.tables — continuation/appendix: overflow tables only
 *  L09 register.index  — folder register / chronological index sheet
 */

import type { Surface, SurfaceTable } from "@/types/archive";

export type LayoutId =
  | "L01.main"
  | "L02.text"
  | "L03.plate"
  | "L04.dual"
  | "L05.compound"
  | "L06.card"
  | "L07.stub"
  | "L08.appendix"
  | "L09.register";

export const LAYOUT_LABEL: Record<LayoutId, string> = {
  "L01.main": "Main sheet",
  "L02.text": "Text sheet",
  "L03.plate": "Plate",
  "L04.dual": "Dual plate",
  "L05.compound": "Compound",
  "L06.card": "Sparse card",
  "L07.stub": "Fallback stub",
  "L08.appendix": "Appendix",
  "L09.register": "Register",
};

/** Placement variants for the L01 main sheet (same slots, different grid). */
export type SheetVariant = "img-right" | "img-left" | "img-top";

/**
 * An image may only drive layout when it can actually be displayed: a
 * permitted state (IMG01 / IMG03) AND a real URL in the payload.
 * IMG00/IMG02 are still image-presence states: they reserve an image bay, but
 * render an empty rights/source frame instead of a bitmap. IMG04 is the only
 * no-image-frame state.
 */
export function isRenderableImage(img?: {
  state?: string;
  url?: string | null;
}): boolean {
  return (
    (img?.state === "IMG01" || img?.state === "IMG03") && Boolean(img?.url)
  );
}

/** Count of additional renderable plates carried on `images`. */
export function renderableExtraCount(s: Surface): number {
  return (s.images ?? []).filter((im) => isRenderableImage(im)).length;
}

/** Deterministic layout choice from payload attributes (never random). */
export function selectLayout(s: Surface): LayoutId {
  if (s.surfaceType === "fallback_stub") return "L07.stub";
  if (s.surfaceType === "card") return "L06.card";
  if (s.templateId === "sheet.compound.v0" || s.layoutHint === "compound") {
    return "L05.compound";
  }

  if (s.image.state === "IMG00" || s.image.state === "IMG02") {
    return "L01.main";
  }

  if (s.image.state === "IMG04") {
    return "L02.text";
  }

  // Image-led layouts ONLY when the image truly renders.
  if (isRenderableImage(s.image)) {
    if (s.layoutHint === "dual" || renderableExtraCount(s) >= 1) {
      return "L04.dual";
    }
    if (s.layoutHint === "plate") return "L03.plate";
    return "L01.main";
  }

  // No displayable image evidence and no explicit image-presence state.
  return "L02.text";
}

/**
 * Stable variant selection for the canonical main sheet. Uses a hash of the
 * surface id so a given record always renders the same variant.
 */
export function sheetVariant(s: Surface): SheetVariant {
  let h = 0;
  for (const ch of s.surfaceId) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const variants: SheetVariant[] = ["img-right", "img-left", "img-top"];
  return variants[h % variants.length];
}

// ---------------------------------------------------------------------------
// Slot contract — what every page can surface (the generator fills these).
// ---------------------------------------------------------------------------

export const TABLE_ORDER = [
  "SOURCE",
  "NORMALIZED",
  "RIGHTS",
  "CLASSIFICATION",
  "RELATIONS",
  "CITATIONS",
] as const;

/** Tables in fixed canonical order, only those present in the payload. */
export function orderedTables(s: Surface): SurfaceTable[] {
  const byKind = new Map(s.tables.map((t) => [t.kind, t]));
  return TABLE_ORDER.map((k) => byKind.get(k)).filter(
    (t): t is SurfaceTable => Boolean(t),
  );
}

/** Weight (row-units) of a table for pagination budgeting. */
export function tableWeight(t: SurfaceTable): number {
  return t.rows.length + 1; // +1 for the kicker/header line
}
