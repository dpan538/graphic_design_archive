import type { ImageState, Surface } from "@/types/archive";
import type { AppendixLayoutId } from "./appendix-layout";
import type { MainSheetLayoutId } from "./main-sheet-layout";
import type { Leaf } from "./paginate";
import type { TextPageLayoutId } from "./text-page-layout";

export type LayoutLevel =
  | "IMG00"
  | "IMG01"
  | "IMG02"
  | "IMG03"
  | "IMG04"
  | "CTX"
  | "META"
  | "BIB";

export type OverflowPolicy =
  | "none"
  | "appendix"
  | "paginate"
  | "ledger"
  | "clip_optional";

export interface LayoutVariantContract {
  name: string;
  minFontRem: {
    body: number;
    metadata: number;
    micro: number;
  };
  maxColumns: number;
  maxTitleLines: number;
  maxBodyLines: number;
  maxTableRows: number;
  maxMetadataRows: number;
  maxCitationRows: number;
  requiredFields: string[];
  allowTruncation: boolean;
  allowImageFrame: boolean;
  overflowPolicy: OverflowPolicy;
  compatibleImageStates: ImageState[];
}

export interface LeafLayoutContract extends LayoutVariantContract {
  level: LayoutLevel;
}

const IMAGE_STATES: ImageState[] = ["IMG00", "IMG01", "IMG02", "IMG03", "IMG04"];
const VISIBLE_IMAGE_STATES: ImageState[] = ["IMG01", "IMG02", "IMG03"];

export const LAYOUT_LEVEL_VARIANTS: Record<LayoutLevel, LayoutVariantContract[]> = {
  IMG00: [
    {
      name: "rights_placeholder",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 2,
      maxTitleLines: 3,
      maxBodyLines: 7,
      maxTableRows: 6,
      maxMetadataRows: 5,
      maxCitationRows: 2,
      requiredFields: ["notice", "source", "rights"],
      allowTruncation: true,
      allowImageFrame: true,
      overflowPolicy: "appendix",
      compatibleImageStates: ["IMG00"],
    },
  ],
  IMG01: [
    {
      name: "controlled_thumbnail",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 2,
      maxTitleLines: 3,
      maxBodyLines: 6,
      maxTableRows: 5,
      maxMetadataRows: 4,
      maxCitationRows: 2,
      requiredFields: ["thumb", "credit", "source"],
      allowTruncation: true,
      allowImageFrame: true,
      overflowPolicy: "appendix",
      compatibleImageStates: ["IMG01"],
    },
  ],
  IMG02: [
    {
      name: "source_hosted_viewer",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 2,
      maxTitleLines: 3,
      maxBodyLines: 6,
      maxTableRows: 5,
      maxMetadataRows: 4,
      maxCitationRows: 2,
      requiredFields: ["viewer", "credit", "source"],
      allowTruncation: true,
      allowImageFrame: true,
      overflowPolicy: "appendix",
      compatibleImageStates: ["IMG02"],
    },
  ],
  IMG03: [
    {
      name: "open_image",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 2,
      maxTitleLines: 3,
      maxBodyLines: 7,
      maxTableRows: 6,
      maxMetadataRows: 5,
      maxCitationRows: 3,
      requiredFields: ["image", "credit", "license", "source"],
      allowTruncation: true,
      allowImageFrame: true,
      overflowPolicy: "appendix",
      compatibleImageStates: ["IMG03"],
    },
  ],
  IMG04: [
    {
      name: "text_only",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 1,
      maxTitleLines: 4,
      maxBodyLines: 18,
      maxTableRows: 0,
      maxMetadataRows: 6,
      maxCitationRows: 0,
      requiredFields: ["title", "source", "text"],
      allowTruncation: false,
      allowImageFrame: false,
      overflowPolicy: "paginate",
      compatibleImageStates: ["IMG04"],
    },
  ],
  CTX: [
    {
      name: "context_surface",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 2,
      maxTitleLines: 4,
      maxBodyLines: 14,
      maxTableRows: 3,
      maxMetadataRows: 5,
      maxCitationRows: 1,
      requiredFields: ["title", "context"],
      allowTruncation: false,
      allowImageFrame: false,
      overflowPolicy: "paginate",
      compatibleImageStates: IMAGE_STATES,
    },
  ],
  META: [
    {
      name: "metadata_sheet",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 2,
      maxTitleLines: 3,
      maxBodyLines: 6,
      maxTableRows: 8,
      maxMetadataRows: 10,
      maxCitationRows: 2,
      requiredFields: ["record", "metadata"],
      allowTruncation: true,
      allowImageFrame: false,
      overflowPolicy: "ledger",
      compatibleImageStates: IMAGE_STATES,
    },
  ],
  BIB: [
    {
      name: "bibliography_entry",
      minFontRem: { body: 0.72, metadata: 0.62, micro: 0.56 },
      maxColumns: 1,
      maxTitleLines: 3,
      maxBodyLines: 10,
      maxTableRows: 4,
      maxMetadataRows: 6,
      maxCitationRows: 6,
      requiredFields: ["source", "citation"],
      allowTruncation: false,
      allowImageFrame: false,
      overflowPolicy: "paginate",
      compatibleImageStates: IMAGE_STATES,
    },
  ],
};

function firstVariant(level: LayoutLevel): LayoutVariantContract {
  return LAYOUT_LEVEL_VARIANTS[level][0];
}

function imageLevel(surface?: Surface): LayoutLevel {
  const state = surface?.image.state;
  return state && IMAGE_STATES.includes(state) ? state : "CTX";
}

function appendixLevel(layoutId?: AppendixLayoutId): LayoutLevel {
  switch (layoutId) {
    case "AX01.rights":
      return "IMG00";
    case "AX02.citation":
      return "BIB";
    case "AX03.relations":
    case "AX06.typed-index":
      return "META";
    case "AX04.context":
    case "AX05.statement":
    default:
      return "CTX";
  }
}

function contractForMainSheet(
  surface: Surface | undefined,
  layoutId?: MainSheetLayoutId,
): LeafLayoutContract {
  const level = imageLevel(surface);
  const base = firstVariant(level);
  const denseLedger = layoutId === "MS01.protocol-ledger" || layoutId === "MS04.grid-register";
  return {
    ...base,
    level,
    name: layoutId ?? base.name,
    maxBodyLines: denseLedger ? Math.min(base.maxBodyLines, 6) : base.maxBodyLines,
    maxTableRows: denseLedger ? Math.min(base.maxTableRows, 5) : base.maxTableRows,
    maxMetadataRows: denseLedger ? Math.min(base.maxMetadataRows, 4) : base.maxMetadataRows,
    overflowPolicy: level === "IMG04" ? "paginate" : "appendix",
    allowImageFrame:
      level === "IMG00" || (surface?.image.url ? VISIBLE_IMAGE_STATES.includes(surface.image.state) : false),
  };
}

function contractForTextPage(
  surface: Surface | undefined,
  layoutId?: TextPageLayoutId,
): LeafLayoutContract {
  const level = surface?.image.state === "IMG04" ? "IMG04" : "CTX";
  const base = firstVariant(level);
  const longForm = layoutId === "TP09.spread-body" || layoutId === "TP16.source-dossier";
  return {
    ...base,
    level,
    name: layoutId ?? base.name,
    maxBodyLines: longForm ? 22 : base.maxBodyLines,
    maxMetadataRows: level === "IMG04" ? 7 : base.maxMetadataRows,
    allowImageFrame: false,
    allowTruncation: false,
    overflowPolicy: "paginate",
  };
}

export function layoutContractForLeaf(leaf: Leaf): LeafLayoutContract {
  switch (leaf.type) {
    case "main":
      return contractForMainSheet(leaf.surface, leaf.mainSheetLayoutId);
    case "text":
      return contractForTextPage(leaf.surface, leaf.textPageLayoutId);
    case "appendix": {
      const level = appendixLevel(leaf.appendixLayoutId);
      const base = firstVariant(level);
      return {
        ...base,
        level,
        name: leaf.appendixLayoutId ?? base.name,
        overflowPolicy: level === "META" ? "ledger" : base.overflowPolicy,
        allowImageFrame: level === "IMG00" && leaf.surface?.image.state === "IMG00",
      };
    }
    case "subsheet": {
      const base = firstVariant("META");
      return { ...base, level: "META", name: leaf.subSheetLayoutId ?? base.name };
    }
    case "slip": {
      const base = firstVariant("BIB");
      return { ...base, level: "BIB", name: leaf.slipLayoutId ?? base.name };
    }
    case "reading_note": {
      const base = firstVariant("CTX");
      return {
        ...base,
        level: "CTX",
        name: leaf.readingNoteLayoutId ?? "reading_note",
        maxColumns: 1,
        maxBodyLines: 12,
        overflowPolicy: "paginate",
      };
    }
    case "bookmark": {
      const base = firstVariant("CTX");
      return {
        ...base,
        level: "CTX",
        name: "bookmark",
        allowTruncation: true,
        overflowPolicy: "clip_optional",
      };
    }
    case "register": {
      const base = firstVariant("META");
      return {
        ...base,
        level: "META",
        name: "register",
        maxTableRows: 17,
        overflowPolicy: "paginate",
      };
    }
    default: {
      const base = firstVariant(imageLevel(leaf.surface));
      return { ...base, level: imageLevel(leaf.surface), name: leaf.layoutId ?? base.name };
    }
  }
}

export function layoutContractDataAttrs(contract: LeafLayoutContract) {
  return {
    "data-level": contract.level,
    "data-variant": contract.name,
    "data-overflow-policy": contract.overflowPolicy,
    "data-min-body-rem": String(contract.minFontRem.body),
    "data-min-metadata-rem": String(contract.minFontRem.metadata),
    "data-min-micro-rem": String(contract.minFontRem.micro),
    "data-max-columns": String(contract.maxColumns),
    "data-max-title-lines": String(contract.maxTitleLines),
    "data-max-body-lines": String(contract.maxBodyLines),
    "data-max-table-rows": String(contract.maxTableRows),
    "data-max-metadata-rows": String(contract.maxMetadataRows),
    "data-max-citation-rows": String(contract.maxCitationRows),
    "data-required-fields": contract.requiredFields.join(" "),
    "data-compatible-image-states": contract.compatibleImageStates.join(" "),
    "data-allow-truncation": String(contract.allowTruncation),
    "data-allow-image-frame": String(contract.allowImageFrame),
  };
}

export function estimateVariantMinBox(variant: LayoutVariantContract) {
  return {
    width: variant.minFontRem.body * 16 * 15 * variant.maxColumns + 40,
    height:
      variant.minFontRem.body * 16 * Math.max(variant.requiredFields.length, 1) * 1.5 + 20,
  };
}

export function selectBestVariantForBox(
  variants: LayoutVariantContract[],
  width: number,
  height: number,
) {
  return (
    variants.find((variant) => {
      const min = estimateVariantMinBox(variant);
      return width >= min.width && height >= min.height;
    }) ?? variants[variants.length - 1]
  );
}
