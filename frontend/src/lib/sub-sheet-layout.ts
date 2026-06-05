export type SubSheetLayoutId =
  | "SS01.schedule-index"
  | "SS02.redline-cv"
  | "SS03.day-column"
  | "SS04.resume-dossier"
  | "SS05.layered-menu"
  | "SS06.punched-letter"
  | "SS07.invoice-ledger"
  | "SS08.cv-sections";

export type SubSheetLayoutSpec = {
  label: string;
  relativeWeight: 0.9;
  role: string;
};

export const SUB_SHEET_LAYOUTS: Record<SubSheetLayoutId, SubSheetLayoutSpec> = {
  "SS01.schedule-index": {
    label: "Source scroll index",
    relativeWeight: 0.9,
    role: "Japanese/Chinese-influenced vertical-axis index for records with enough metadata to read as a source scroll.",
  },
  "SS02.redline-cv": {
    label: "Ink seal dossier",
    relativeWeight: 0.9,
    role: "Ink-blue evidence dossier with seal logic, compact image proof, and source/classification blocks.",
  },
  "SS03.day-column": {
    label: "Day column",
    relativeWeight: 0.9,
    role: "Vertical event-index sheet with oversized chronology, source fragments, and a modest evidence stamp.",
  },
  "SS04.resume-dossier": {
    label: "Resume dossier",
    relativeWeight: 0.9,
    role: "Resume-like archival summary for a single object, balancing large identity with compact evidence fields.",
  },
  "SS05.layered-menu": {
    label: "Layered menu",
    relativeWeight: 0.9,
    role: "Stacked-paper source menu with offset side registers and a compact evidence stamp.",
  },
  "SS06.punched-letter": {
    label: "Punched letter",
    relativeWeight: 0.9,
    role: "Stationery-like letter sheet using margin punch marks, address blocks, and a restrained table.",
  },
  "SS07.invoice-ledger": {
    label: "Invoice ledger",
    relativeWeight: 0.9,
    role: "Sparse invoice-style archive ledger with large negative space and a precise source/payment register.",
  },
  "SS08.cv-sections": {
    label: "CV sections",
    relativeWeight: 0.9,
    role: "Sectioned CV-like source summary with thick dividers, compact portrait evidence, and grouped metadata.",
  },
};

export const SUB_SHEET_LAYOUT_ORDER: SubSheetLayoutId[] = [
  "SS01.schedule-index",
  "SS02.redline-cv",
  "SS03.day-column",
  "SS04.resume-dossier",
  "SS05.layered-menu",
  "SS06.punched-letter",
  "SS07.invoice-ledger",
  "SS08.cv-sections",
];

type SubSheetSurfaceLike = {
  surfaceId: string;
  completenessScore?: number;
  descriptionSummary?: string;
  sourceDescription?: string;
  readingTextLength?: number;
  image?: {
    state?: string;
    url?: string | null;
  };
  folders?: unknown[];
  tables?: Array<{ kind?: string; rows?: unknown[] }>;
};

function stableHash(value: string): number {
  let hash = 2166136261;
  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function textLength(surface: SubSheetSurfaceLike): number {
  return (
    surface.readingTextLength ??
    [surface.descriptionSummary, surface.sourceDescription].filter(Boolean).join(" ").length
  );
}

function rowCount(surface: SubSheetSurfaceLike, kind?: string): number {
  return (surface.tables ?? []).reduce((total, table) => {
    if (kind && table.kind !== kind) return total;
    return total + (table.rows?.length ?? 0);
  }, 0);
}

function firstDifferent(
  candidates: SubSheetLayoutId[],
  previous?: SubSheetLayoutId | null,
): SubSheetLayoutId {
  return candidates.find((candidate) => candidate !== previous) ?? candidates[0];
}

export function selectSubSheetLayout(
  surface: SubSheetSurfaceLike,
  previous?: SubSheetLayoutId | null,
): SubSheetLayoutId {
  const hash = stableHash(surface.surfaceId);
  const imageState = surface.image?.state ?? "IMG04";
  const hasRenderableImage =
    Boolean(surface.image?.url) &&
    (imageState === "IMG01" || imageState === "IMG02" || imageState === "IMG03");
  const rows = rowCount(surface);
  const sourceRows = rowCount(surface, "SOURCE");
  const rightsRows = rowCount(surface, "RIGHTS");
  const folders = surface.folders?.length ?? 0;
  const length = textLength(surface);
  const completeness = surface.completenessScore ?? 0;

  if (imageState === "IMG00" || rightsRows >= 5) {
    return firstDifferent(["SS02.redline-cv", "SS07.invoice-ledger", "SS08.cv-sections"], previous);
  }

  if (rows >= 28 || folders >= 4) {
    return firstDifferent(
      hash % 2 === 0
        ? ["SS08.cv-sections", "SS04.resume-dossier", "SS01.schedule-index"]
        : ["SS04.resume-dossier", "SS08.cv-sections", "SS07.invoice-ledger"],
      previous,
    );
  }

  if (sourceRows >= 6 || length >= 700) {
    return firstDifferent(
      hash % 3 === 0
        ? ["SS06.punched-letter", "SS05.layered-menu", "SS03.day-column"]
        : ["SS05.layered-menu", "SS06.punched-letter", "SS01.schedule-index"],
      previous,
    );
  }

  if (hasRenderableImage && completeness >= 65) {
    return firstDifferent(
      hash % 2 === 0
        ? ["SS03.day-column", "SS01.schedule-index", "SS05.layered-menu"]
        : ["SS01.schedule-index", "SS03.day-column", "SS04.resume-dossier"],
      previous,
    );
  }

  const cycle: SubSheetLayoutId[] = [
    "SS01.schedule-index",
    "SS05.layered-menu",
    "SS03.day-column",
    "SS07.invoice-ledger",
    "SS06.punched-letter",
    "SS08.cv-sections",
    "SS02.redline-cv",
    "SS04.resume-dossier",
  ];
  const first = cycle[hash % cycle.length];
  return firstDifferent(
    [first, "SS01.schedule-index", "SS05.layered-menu", "SS03.day-column", "SS08.cv-sections"],
    previous,
  );
}

export function subSheetFrameClass(_layoutId: SubSheetLayoutId): string {
  return "leaf--sub-sheet-portrait";
}
