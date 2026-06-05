/**
 * No-scroll pagination engine.
 *
 * Because the viewport never scrolls, content is packed into fixed-capacity
 * leaves at build time. Each leaf is a single physical (A4) page; the reader
 * shows one leaf (single) or two adjacent leaves (facing spread). Overflow
 * tables may create appendix leaves (AX01-AX06). A folder always opens on one or more
 * register/index leaves (L09). Pagination is deterministic.
 */

import type { Folder, Surface, SurfaceTable } from "@/types/archive";
import {
  type LayoutId,
  type SheetVariant,
  orderedTables,
  selectLayout,
  sheetVariant,
  tableWeight,
} from "./layout";
import {
  type ChronologyGroup,
  getSurfacesForFolder,
  groupByDecade,
  sortChronologically,
} from "./archive-data";
import {
  type AppendixLayoutId,
  fallbackAppendixLayout,
  selectAppendixLayout,
} from "./appendix-layout";
import {
  type ReadingNoteLayoutId,
  selectReadingNoteLayout,
} from "./reading-note-layout";
import {
  type ArchiveCardLayoutId,
  selectArchiveCardLayout,
} from "./card-asset-layout";
import {
  type SourceSlipLayoutId,
  selectSourceSlipLayout,
} from "./slip-layout";
import {
  selectTextPageLayout,
  type TextPageLayoutId,
} from "./text-page-layout";
import {
  selectMainSheetLayout,
  type MainSheetLayoutId,
} from "./main-sheet-layout";
import {
  selectSubSheetLayout,
  type SubSheetLayoutId,
} from "./sub-sheet-layout";

export interface Leaf {
  /** Stable id for React keys and jump targets. */
  id: string;
  type: "register" | "bookmark" | "reading_note" | "main" | "subsheet" | "text" | "appendix" | "slip";
  folder?: Folder;
  surface?: Surface;
  layoutId?: LayoutId;
  mainSheetLayoutId?: MainSheetLayoutId;
  subSheetLayoutId?: SubSheetLayoutId;
  appendixLayoutId?: AppendixLayoutId;
  readingNoteLayoutId?: ReadingNoteLayoutId;
  textPageLayoutId?: TextPageLayoutId;
  cardLayoutId?: ArchiveCardLayoutId;
  slipLayoutId?: SourceSlipLayoutId;
  variant?: SheetVariant;
  /** Tables rendered on this leaf (subset of the surface's tables). */
  tables?: SurfaceTable[];
  /** 1-based page within the surface, and the surface's total page count. */
  surfacePageNumber?: number;
  surfacePageCount?: number;
  /** Register leaf: decade groups shown on this page + register paging. */
  regGroups?: ChronologyGroup[];
  regPageNumber?: number;
  regPageCount?: number;
}

function isTextOnlyImageState(surface: Surface): boolean {
  return surface.image.state === "IMG04";
}

/** Table row-unit budget for the FIRST (layout) leaf of a surface. */
function mainTableBudget(layoutId: LayoutId): number {
  switch (layoutId) {
    case "L02.text":
      return 0; // text reading page; all tables flow to appendix
    case "L03.plate":
      return 5;
    case "L04.dual":
      return 6;
    case "L05.compound":
      return 5;
    case "L06.card":
      return 9;
    case "L07.stub":
      return 10;
    case "L01.main":
    default:
      return 8;
  }
}

/** Row budget for a register/index leaf (the first page reserves title space). */
const REGISTER_BUDGET = 17;
const REGISTER_FIRST_RESERVE = 7;

function packMainTables(tables: SurfaceTable[], mainBudget: number): SurfaceTable[] {
  const main: SurfaceTable[] = [];
  let used = 0;
  // A zero budget means the layout's first leaf is text-only (no tables).
  if (mainBudget > 0) {
    for (let i = 0; i < tables.length; i++) {
      const w = tableWeight(tables[i]);
      if (main.length > 0 && used + w > mainBudget) break;
      main.push(tables[i]);
      used += w;
    }
  }
  return main;
}

interface AppendixPacket {
  layoutId: AppendixLayoutId;
  tables: SurfaceTable[];
}

function tableByKind(tables: SurfaceTable[], kind: string): SurfaceTable | undefined {
  return tables.find((table) => table.kind === kind);
}

function readingLength(surface: Surface): number {
  if (typeof surface.readingTextLength === "number") return surface.readingTextLength;
  return [
    surface.descriptionSummary,
    surface.sourceDescription,
    surface.sourceNotes,
    surface.sourceSubjects,
  ]
    .filter(Boolean)
    .join(" ").length;
}

function cardSupportLength(surface: Surface): number {
  return [
    surface.descriptionSummary,
    surface.sourceDescription,
    surface.sourceNotes,
    surface.citationBasis,
  ]
    .filter(Boolean)
    .join(" ").length;
}

function needsSlipLeaf(surface: Surface): boolean {
  if (surface.surfaceType !== "card") return false;
  const sourceRows =
    surface.tables.find((table) => table.kind === "SOURCE")?.rows.length ?? 0;
  const citationRows =
    surface.tables.find((table) => table.kind === "CITATIONS")?.rows.length ?? 0;
  const rightsRows =
    surface.tables.find((table) => table.kind === "RIGHTS")?.rows.length ?? 0;
  const evidenceRows = sourceRows + citationRows + rightsRows;
  return cardSupportLength(surface) >= 320 && evidenceRows <= 10;
}

function stableHash(value: string): number {
  let hash = 2166136261;
  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function needsTextLeaf(surface: Surface, layoutId: LayoutId): boolean {
  if (layoutId === "L02.text") return false;
  if (surface.surfaceType !== "sheet") return false;
  return true;
}

function shouldRenderAsSubSheet(surface: Surface): boolean {
  if (surface.surfaceType !== "sheet") return false;
  return (
    surface.publicationRole === "support_packet_appendix_text" ||
    surface.publicationRole === "merge_candidate_support_packet" ||
    surface.publicationRole === "thin_visual_support_packet" ||
    surface.surfaceDisposition === "support_packet_appendix_text" ||
    surface.surfaceDisposition === "merge_candidate_support_packet" ||
    surface.surfaceDisposition === "thin_visual_support_packet" ||
    surface.layoutHint === "support_packet" ||
    surface.layoutHint === "merge_candidate"
  );
}

function isTextCapableSheet(surface: Surface): boolean {
  if (surface.surfaceType !== "sheet") return false;
  const layoutId = selectLayout(surface);
  return layoutId === "L02.text" || needsTextLeaf(surface, layoutId);
}

/**
 * Appendix leaves carry evidence ledgers that should not turn the text page
 * back into a specification sheet. One surface gets at most one appendix packet;
 * the packet type follows AX01-AX06 priorities.
 */
function appendixPacketFor(surface: Surface, tables: SurfaceTable[]): AppendixPacket | null {
  if (surface.surfaceType !== "sheet") return null;

  const relations = tableByKind(tables, "RELATIONS");
  const citations = tableByKind(tables, "CITATIONS");
  const rights = tableByKind(tables, "RIGHTS");
  const source = tableByKind(tables, "SOURCE");
  const normalized = tableByKind(tables, "NORMALIZED");
  const classification = tableByKind(tables, "CLASSIFICATION");
  const imageState = surface.image.state;
  const totalRows = tables.reduce((total, table) => total + table.rows.length, 0);
  const folderCount = surface.folders.length;
  const childCount = surface.compoundChildren?.length ?? 0;
  const sourceTextLength = readingLength(surface);
  const sourceLinks = citations?.rows.find(([label]) => /source links?|source urls?/i.test(label))?.[1] ?? "";
  const multiSourceList = (sourceLinks.match(/https?:\/\//g) ?? []).length >= 2;
  const hash = stableHash(surface.surfaceId);
  const explicitProtocolNote =
    /manual review|protocol-sensitive|source[- ]?only|suppress|sensitive/i.test(
      [
        surface.uncertaintyNote,
        surface.historicalContextNote,
        surface.classificationRationale,
        surface.rights.label,
        surface.citationBasis,
      ]
        .filter(Boolean)
        .join(" "),
    );
  const sourcePolicyContext = imageState === "IMG02" && sourceTextLength >= 1500 && hash % 4 === 0;
  const displayPolicy = surface.rights.displayPolicy;
  const nonBlankRightsEvidence =
    (imageState === "IMG01" || imageState === "IMG02" || imageState === "IMG03") &&
    (displayPolicy !== "open_image_frame" || !surface.reviewGates.rightsReviewed) &&
    sourceTextLength >= 900 &&
    hash % 6 === 0;

  if (imageState === "IMG00") {
    return {
      layoutId: "AX01.rights",
      tables: [rights, source, citations].filter((table): table is SurfaceTable => Boolean(table)),
    };
  }

  if (multiSourceList || childCount >= 3) {
    return {
      layoutId: "AX02.citation",
      tables: [citations, source].filter((table): table is SurfaceTable => Boolean(table)),
    };
  }

  if ((relations && relations.rows.length > 4) || folderCount >= 4 || childCount > 0) {
    return {
      layoutId: "AX03.relations",
      tables: [classification, relations].filter((table): table is SurfaceTable => Boolean(table)),
    };
  }

  if (nonBlankRightsEvidence) {
    return {
      layoutId: "AX01.rights",
      tables: [rights, source, citations].filter((table): table is SurfaceTable => Boolean(table)),
    };
  }

  if (explicitProtocolNote || sourcePolicyContext) {
    return {
      layoutId: "AX04.context",
      tables: [rights, source, classification].filter((table): table is SurfaceTable => Boolean(table)),
    };
  }

  if (totalRows >= 30 && sourceTextLength >= 900 && hash % 5 === 0) {
    const dossierTables = [source, normalized, rights, citations, classification].filter(
      (table): table is SurfaceTable => Boolean(table),
    );
    return {
      layoutId: hash % 3 === 0 ? "AX06.typed-index" : "AX05.statement",
      tables: dossierTables.length ? dossierTables : tables,
    };
  }

  return null;
}

/** Build the leaf sequence for a single surface (no folder register). */
export function paginateSurface(surface: Surface): Leaf[] {
  if (surface.surfaceType === "card") {
    const cardLayoutId = selectArchiveCardLayout(surface);
    const leaves: Leaf[] = [
      {
        id: `${surface.surfaceId}#card`,
        type: "main",
        surface,
        layoutId: "L06.card",
        cardLayoutId,
        tables: orderedTables(surface),
        surfacePageNumber: 1,
        surfacePageCount: needsSlipLeaf(surface) ? 2 : 1,
      },
    ];
    if (needsSlipLeaf(surface)) {
      const slipLayoutId = selectSourceSlipLayout(surface, cardLayoutId);
      leaves.push({
        id: `${surface.surfaceId}#slip`,
        type: "slip",
        surface,
        slipLayoutId,
        cardLayoutId,
        surfacePageNumber: 2,
        surfacePageCount: 2,
      });
    }
    return leaves;
  }

  const layoutId = selectLayout(surface);
  const variant = sheetVariant(surface);
  const tables = orderedTables(surface);
  const main = packMainTables(tables, mainTableBudget(layoutId));
  const textLeaf = needsTextLeaf(surface, layoutId);
  const appendixPacket = appendixPacketFor(surface, tables);
  const appendix = appendixPacket
    ? [
        {
          layoutId: appendixPacket.layoutId,
          tables: appendixPacket.tables,
        },
      ]
    : [];

  const pageCount = 1 + (textLeaf ? 1 : 0) + appendix.length;
  const firstLeafIsText = layoutId === "L02.text" || isTextOnlyImageState(surface);
  const firstLeafIsSubSheet = !firstLeafIsText && shouldRenderAsSubSheet(surface);
  const leaves: Leaf[] = [
    {
      id: `${surface.surfaceId}#p1`,
      type: firstLeafIsText ? "text" : firstLeafIsSubSheet ? "subsheet" : "main",
      surface,
      layoutId,
      mainSheetLayoutId:
        !firstLeafIsText &&
        !firstLeafIsSubSheet &&
        (layoutId === "L01.main" || layoutId === "L03.plate" || layoutId === "L04.dual")
          ? selectMainSheetLayout(surface)
          : undefined,
      subSheetLayoutId: firstLeafIsSubSheet
        ? selectSubSheetLayout(surface)
        : undefined,
      textPageLayoutId: firstLeafIsText ? selectTextPageLayout(surface) : undefined,
      variant,
      tables: main,
      surfacePageNumber: 1,
      surfacePageCount: pageCount,
    },
  ];

  let nextPageNumber = 2;
  if (textLeaf) {
    leaves.push({
      id: `${surface.surfaceId}#text`,
      type: "text",
      surface,
      layoutId: "L02.text",
      textPageLayoutId: selectTextPageLayout(surface),
      variant,
      tables: [],
      surfacePageNumber: nextPageNumber,
      surfacePageCount: pageCount,
    });
    nextPageNumber += 1;
  }

  appendix.forEach((page, idx) => {
    leaves.push({
      id: `${surface.surfaceId}#p${nextPageNumber + idx}`,
      type: "appendix",
      surface,
      appendixLayoutId: page.layoutId,
      tables: page.tables,
      surfacePageNumber: nextPageNumber + idx,
      surfacePageCount: pageCount,
    });
  });

  return leaves;
}

/** Chunk decade groups into register pages by a row budget (groups kept whole). */
function registerSurfaceWeight(surface: Surface): number {
  let weight = 1;
  const date = surface.dateText || "";
  const title = surface.title || "";
  if (date.length >= 18) weight += 1;
  if (title.length >= 54) weight += 1;
  if (/[\u3040-\u30ff\u3400-\u9fff]/.test(title) && title.length >= 18) weight += 1;
  return Math.min(weight, 3);
}

function registerGroupWeight(group: ChronologyGroup): number {
  return (
    1 +
    group.surfaces.reduce(
      (total, surface) => total + registerSurfaceWeight(surface),
      0,
    )
  );
}

function packRegister(groups: ChronologyGroup[]): ChronologyGroup[][] {
  const pages: ChronologyGroup[][] = [];
  let page: ChronologyGroup[] = [];
  // First page also carries the folder title + scope; reserve room for it.
  let used = REGISTER_FIRST_RESERVE;
  for (const g of groups) {
    const w = registerGroupWeight(g);
    if (page.length > 0 && used + w > REGISTER_BUDGET) {
      pages.push(page);
      page = [];
      used = 0;
    }
    page.push(g);
    used += w;
  }
  if (page.length > 0) pages.push(page);
  return pages.length > 0 ? pages : [[]];
}

/**
 * Build the full reading sequence for an opened folder:
 * one or more register leaves (L09), then every member surface in
 * chronological order, each expanded into its own leaves.
 */
export function paginateFolder(folder: Folder): Leaf[] {
  const surfaces = sortChronologically(getSurfacesForFolder(folder));
  const groups = groupByDecade(surfaces);
  const regPages = packRegister(groups);
  let previousAppendixSignature: string | null = null;
  let previousAppendixLayoutId: AppendixLayoutId | null = null;
  let previousMainSheetLayoutId: MainSheetLayoutId | null = null;
  let previousSubSheetLayoutId: SubSheetLayoutId | null = null;
  const attachmentPlan = folderBookmarkAttachments(folder, surfaces);

  const leaves: Leaf[] = regPages.map((regGroups, idx) => ({
    id: `${folder.folderId}#register-${idx + 1}`,
    type: "register",
    folder,
    regGroups,
    regPageNumber: idx + 1,
    regPageCount: regPages.length,
  }));
  leaves.push({
    id: `${folder.folderId}#reading-note`,
    type: "reading_note",
    folder,
    readingNoteLayoutId: selectReadingNoteLayout(folder),
  });

  for (const surface of surfaces) {
    let surfaceLeaves = paginateSurface(surface);
    const mainLeaf = surfaceLeaves.find((leaf) => leaf.type === "main");
    if (
      mainLeaf &&
      (mainLeaf.layoutId === "L01.main" ||
        mainLeaf.layoutId === "L03.plate" ||
        mainLeaf.layoutId === "L04.dual")
    ) {
      mainLeaf.mainSheetLayoutId = selectMainSheetLayout(
        surface,
        previousMainSheetLayoutId,
      );
      previousMainSheetLayoutId = mainLeaf.mainSheetLayoutId;
    }
    const subSheetLeaf = surfaceLeaves.find((leaf) => leaf.type === "subsheet");
    if (subSheetLeaf) {
      subSheetLeaf.subSheetLayoutId = selectSubSheetLayout(
        surface,
        previousSubSheetLayoutId,
      );
      previousSubSheetLayoutId = subSheetLeaf.subSheetLayoutId;
    }
    const attachmentType = attachmentPlan.get(surface.surfaceId);
    if (attachmentType) {
      surfaceLeaves = attachTextCompanion(surfaceLeaves, surface, folder, attachmentType);
    }
    const appendixLeaf = surfaceLeaves.find((leaf) => leaf.type === "appendix");
    if (appendixLeaf?.appendixLayoutId) {
      appendixLeaf.appendixLayoutId = resolvedAppendixLayout(
        surface,
        appendixLeaf.tables ?? [],
        appendixLeaf.appendixLayoutId,
        previousAppendixLayoutId,
      );
    }
    const appendixSignature =
      appendixLeaf?.appendixLayoutId === "AX01.rights"
        ? [
            appendixLeaf.appendixLayoutId,
            surface.sourceName,
            surface.image.state,
            surface.rights.displayPolicy,
          ].join("|")
        : null;

    if (appendixSignature && appendixSignature === previousAppendixSignature) {
      const filtered = surfaceLeaves.filter((leaf) => leaf.type !== "appendix");
      filtered.forEach((leaf, index) => {
        if (leaf.surfacePageNumber != null) leaf.surfacePageNumber = index + 1;
        if (leaf.surfacePageCount != null) leaf.surfacePageCount = filtered.length;
      });
      leaves.push(...filtered);
    } else {
      leaves.push(...surfaceLeaves);
    }
    previousAppendixSignature = appendixSignature;
    previousAppendixLayoutId = appendixLeaf?.appendixLayoutId ?? previousAppendixLayoutId;
  }
  return leaves;
}

function folderBookmarkAttachments(
  folder: Folder,
  surfaces: Surface[],
): Map<string, "bookmark"> {
  const candidates = surfaces.filter((surface) => {
    if (surface.surfaceType === "fallback_stub") return true;
    if (surface.completenessScore >= 20) return false;
    if (surface.surfaceType === "card") return false;
    const layoutId = selectLayout(surface);
    return layoutId === "L07.stub" || surface.image.state === "IMG04";
  });
  const attachments = new Map<string, "bookmark">();
  if (candidates.length === 0) return attachments;

  const hash = stableHash(folder.folderId);
  const bookmarkTarget = candidates[hash % candidates.length];
  attachments.set(bookmarkTarget.surfaceId, "bookmark");

  return attachments;
}

function attachTextCompanion(
  surfaceLeaves: Leaf[],
  surface: Surface,
  folder: Folder,
  attachmentType: "bookmark" | "reading_note",
): Leaf[] {
  const appendixLeaf = surfaceLeaves.find((leaf) => leaf.type === "appendix");
  if (appendixLeaf) return surfaceLeaves;

  const attachAfterIndex = surfaceLeaves.findIndex((leaf) => leaf.type === "text");
  const anchorIndex =
    attachAfterIndex >= 0
      ? attachAfterIndex
      : surfaceLeaves.findIndex(
          (leaf) => leaf.type === "text" || (leaf.type === "main" && leaf.layoutId === "L02.text"),
        );
  if (anchorIndex < 0) return surfaceLeaves;

  const attachmentLeaf: Leaf =
    attachmentType === "bookmark"
      ? {
          id: `${surface.surfaceId}#bookmark`,
          type: "bookmark",
          surface,
          folder,
        }
      : {
          id: `${surface.surfaceId}#reading-note`,
          type: "reading_note",
          surface,
          folder,
          readingNoteLayoutId: "RN04.ledger",
        };

  const nextLeaves = [
    ...surfaceLeaves.slice(0, anchorIndex + 1),
    attachmentLeaf,
    ...surfaceLeaves.slice(anchorIndex + 1),
  ];
  nextLeaves.forEach((leaf, index) => {
    leaf.surfacePageNumber = index + 1;
    leaf.surfacePageCount = nextLeaves.length;
  });
  return nextLeaves;
}

function resolvedAppendixLayout(
  surface: Surface,
  evidenceTables: SurfaceTable[],
  current: AppendixLayoutId,
  previous: AppendixLayoutId | null,
): AppendixLayoutId {
  if (!previous || current !== previous) return current;
  const candidates: AppendixLayoutId[] = [
    selectAppendixLayout(surface, evidenceTables, 1),
    selectAppendixLayout(surface, evidenceTables, 2),
    fallbackAppendixLayout(surface, evidenceTables),
    "AX05.statement",
    "AX04.context",
    "AX02.citation",
    "AX03.relations",
    "AX01.rights",
    "AX06.typed-index",
  ];
  return candidates.find((layoutId) => layoutId !== previous) ?? current;
}

/** Map each surface id to the leaf index of its first (main) page. */
export function surfaceLeafIndex(leaves: Leaf[]): Map<string, number> {
  const map = new Map<string, number>();
  leaves.forEach((leaf, i) => {
    if (
      (leaf.type === "main" || leaf.type === "subsheet" || leaf.type === "text") &&
      leaf.surface &&
      !map.has(leaf.surface.surfaceId)
    ) {
      map.set(leaf.surface.surfaceId, i);
    }
  });
  return map;
}

export interface JumpTarget {
  leafIndex: number;
  label: string;
  sublabel: string;
  surfaceId?: string;
}

/** Reader contents-panel jump targets: register + first leaf of each surface. */
export function folderJumpTargets(leaves: Leaf[]): JumpTarget[] {
  const targets: JumpTarget[] = [];
  leaves.forEach((leaf, index) => {
    if (leaf.type === "register" && leaf.folder && leaf.regPageNumber === 1) {
      targets.push({
        leafIndex: index,
        label: "Register / index",
        sublabel: "Folder contents",
      });
    }
    if ((leaf.type === "main" || leaf.type === "subsheet" || leaf.type === "text") && leaf.surface) {
      targets.push({
        leafIndex: index,
        label: leaf.surface.title,
        sublabel: leaf.surface.dateText,
        surfaceId: leaf.surface.surfaceId,
      });
    }
  });
  return targets;
}
