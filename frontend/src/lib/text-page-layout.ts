import type { Surface } from "@/types/archive";
import { isRenderableImage } from "./layout";

export type TextPageLayoutId =
  | "TP01.fragment-field"
  | "TP02.radical-inset"
  | "TP03.editorial-column"
  | "TP04.essay-chorus"
  | "TP05.annotation-grid"
  | "TP06.spread-cover"
  | "TP08.spread-quote"
  | "TP09.spread-body"
  | "TP10.geology-ledger"
  | "TP11.free-horizon"
  | "TP12.perforated-field"
  | "TP14.waiting-plate"
  | "TP16.source-dossier";

function stableHash(value: string): number {
  let hash = 2166136261;
  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function readingLength(surface: Surface): number {
  if (typeof surface.readingTextLength === "number") return surface.readingTextLength;
  return [
    surface.descriptionSummary,
    surface.sourceDescription,
    surface.historicalContextNote,
    surface.classificationRationale,
    surface.sourceNotes,
    surface.sourceSubjects,
    surface.citationBasis,
  ]
    .filter(Boolean)
    .join(" ").length;
}

function renderableImageCount(surface: Surface): number {
  const urls = new Set<string>();
  for (const image of [surface.image, ...(surface.images ?? [])]) {
    if (isRenderableImage(image) && image.url) urls.add(image.url);
  }
  return urls.size;
}

export function isHorizontalTextPageLayout(id: TextPageLayoutId): boolean {
  return id === "TP10.geology-ledger" || id === "TP11.free-horizon";
}

export function textPageFrameClass(id: TextPageLayoutId): string {
  return isHorizontalTextPageLayout(id)
    ? "leaf--text-page leaf--text-page-horizontal"
    : "leaf--text-page leaf--text-page-vertical";
}

export function selectTextPageLayout(surface: Surface): TextPageLayoutId {
  const length = readingLength(surface);
  const imageCount = renderableImageCount(surface);
  const hasImage = imageCount > 0;
  const hash = stableHash(surface.surfaceId);

  if (imageCount >= 3) return "TP16.source-dossier";

  // Horizontal text pages are intentionally rare and only for dense reading
  // leaves. They should not become the default continuation surface.
  if (length >= 1800) {
    return hasImage ? "TP10.geology-ledger" : "TP11.free-horizon";
  }

  if (!hasImage) {
    if (length >= 1200) return "TP09.spread-body";
    if (length >= 760) return "TP08.spread-quote";
    if (length >= 420) return "TP06.spread-cover";
    return "TP12.perforated-field";
  }

  if (length >= 1250) return hash % 2 === 0 ? "TP05.annotation-grid" : "TP04.essay-chorus";
  if (length >= 820) return hash % 2 === 0 ? "TP03.editorial-column" : "TP05.annotation-grid";
  if (length >= 520) return hash % 2 === 0 ? "TP02.radical-inset" : "TP04.essay-chorus";
  return hash % 3 === 0 ? "TP14.waiting-plate" : "TP01.fragment-field";
}
