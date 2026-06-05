import type { Surface } from "@/types/archive";
import { isRenderableImage } from "./layout";

export type ArchiveCardLayoutId =
  | "CARD01.specimen-square"
  | "CARD02.typography-portrait"
  | "CARD03.rights-review"
  | "CARD04.source-wide"
  | "CARD05.publication";

export const ARCHIVE_CARD_LAYOUTS: Record<
  ArchiveCardLayoutId,
  { label: string; priority: "standard" | "restricted" | "support" }
> = {
  "CARD01.specimen-square": {
    label: "Square specimen card",
    priority: "standard",
  },
  "CARD02.typography-portrait": {
    label: "Portrait reading card",
    priority: "standard",
  },
  "CARD03.rights-review": {
    label: "Rights review card",
    priority: "restricted",
  },
  "CARD04.source-wide": {
    label: "Wide source card",
    priority: "support",
  },
  "CARD05.publication": {
    label: "Publication note card",
    priority: "support",
  },
};

export function selectArchiveCardLayout(surface: Surface): ArchiveCardLayoutId {
  if (surface.image.state === "IMG00") return "CARD03.rights-review";
  if (!isRenderableImage(surface.image)) {
    return surface.rights.displayPolicy === "open_image_frame"
      ? "CARD02.typography-portrait"
      : "CARD03.rights-review";
  }
  const textLength = [
    surface.descriptionSummary,
    surface.sourceDescription,
    surface.sourceNotes,
  ]
    .filter(Boolean)
    .join(" ").length;
  if (textLength >= 360) return "CARD04.source-wide";
  if (/periodical|publication|magazine|book|catalog|catalogue/i.test(surface.objectType)) {
    return "CARD05.publication";
  }
  return "CARD01.specimen-square";
}

export function archiveCardFrameClass(layoutId: ArchiveCardLayoutId): string {
  switch (layoutId) {
    case "CARD01.specimen-square":
      return "leaf--card-square";
    case "CARD04.source-wide":
    case "CARD05.publication":
      return "leaf--card-landscape";
    case "CARD02.typography-portrait":
    case "CARD03.rights-review":
    default:
      return "leaf--card-portrait";
  }
}
