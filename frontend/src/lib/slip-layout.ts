import type { Surface } from "@/types/archive";
import type { ArchiveCardLayoutId } from "./card-asset-layout";

export type SourceSlipLayoutId =
  | "SLIP01.square"
  | "SLIP02.portrait"
  | "SLIP03.narrow";

export const SOURCE_SLIP_LAYOUTS: Record<SourceSlipLayoutId, { label: string }> = {
  "SLIP01.square": { label: "Square source slip" },
  "SLIP02.portrait": { label: "Portrait citation slip" },
  "SLIP03.narrow": { label: "Narrow source return slip" },
};

function sourceTextLength(surface: Surface): number {
  return [
    surface.descriptionSummary,
    surface.sourceDescription,
    surface.sourceNotes,
    surface.citationBasis,
  ]
    .filter(Boolean)
    .join(" ")
    .length;
}

export function selectSourceSlipLayout(
  surface: Surface,
  cardLayoutId: ArchiveCardLayoutId,
): SourceSlipLayoutId {
  if (cardLayoutId === "CARD01.specimen-square") return "SLIP01.square";
  if (surface.image.state === "IMG00" || sourceTextLength(surface) >= 320) {
    return "SLIP03.narrow";
  }
  return "SLIP02.portrait";
}

export function sourceSlipFrameClass(layoutId: SourceSlipLayoutId): string {
  switch (layoutId) {
    case "SLIP01.square":
      return "leaf--slip-square";
    case "SLIP03.narrow":
      return "leaf--slip-narrow";
    case "SLIP02.portrait":
    default:
      return "leaf--slip-portrait";
  }
}
