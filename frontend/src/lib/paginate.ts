/**
 * No-scroll pagination engine.
 *
 * Because the viewport never scrolls, content is packed into fixed-capacity
 * leaves at build time. Each leaf is a single physical (A4) page; the reader
 * shows one leaf (single) or two adjacent leaves (facing spread). Overflow
 * tables flow onto appendix leaves (L08). A folder always opens on one or more
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

export interface Leaf {
  /** Stable id for React keys and jump targets. */
  id: string;
  type: "register" | "bookmark" | "main" | "text" | "appendix";
  folder?: Folder;
  surface?: Surface;
  layoutId?: LayoutId;
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

const APPENDIX_BUDGET = 14;
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

function packAppendixTables(tables: SurfaceTable[]): SurfaceTable[][] {
  const appendix: SurfaceTable[][] = [];
  let page: SurfaceTable[] = [];
  let pageUsed = 0;
  for (const table of tables) {
    const w = tableWeight(table);
    if (page.length > 0 && pageUsed + w > APPENDIX_BUDGET) {
      appendix.push(page);
      page = [];
      pageUsed = 0;
    }
    page.push(table);
    pageUsed += w;
  }
  if (page.length > 0) appendix.push(page);
  return appendix;
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

function needsTextLeaf(surface: Surface, layoutId: LayoutId): boolean {
  if (layoutId === "L02.text") return false;
  if (surface.surfaceType !== "sheet") return false;
  return true;
}

/**
 * Appendix leaves are now exceptional evidence pages, not automatic overflow.
 * The payload still carries all six tables for reproducibility; this function
 * decides which tables deserve a separate physical continuation sheet.
 */
function appendixTablesFor(surface: Surface, tables: SurfaceTable[]): SurfaceTable[] {
  if (surface.surfaceType !== "sheet") return [];

  const selected: SurfaceTable[] = [];
  const relations = tableByKind(tables, "RELATIONS");
  const citations = tableByKind(tables, "CITATIONS");
  const rights = tableByKind(tables, "RIGHTS");
  const source = tableByKind(tables, "SOURCE");

  if (surface.image.state === "IMG00" && rights) {
    selected.push(rights);
  }
  if (relations && relations.rows.length > 4) {
    selected.push(relations);
  }
  if (citations && citations.rows.length > 3) {
    selected.push(citations);
  }
  if ((surface.compoundChildren?.length ?? 0) > 8 && source) {
    selected.push(source);
  }

  return selected;
}

/** Build the leaf sequence for a single surface (no folder register). */
export function paginateSurface(surface: Surface): Leaf[] {
  const layoutId = selectLayout(surface);
  const variant = sheetVariant(surface);
  const tables = orderedTables(surface);
  const main = packMainTables(tables, mainTableBudget(layoutId));
  const textLeaf = needsTextLeaf(surface, layoutId);
  const appendix = packAppendixTables(appendixTablesFor(surface, tables));

  const pageCount = 1 + (textLeaf ? 1 : 0) + appendix.length;
  const leaves: Leaf[] = [
    {
      id: `${surface.surfaceId}#p1`,
      type: "main",
      surface,
      layoutId,
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
      variant,
      tables: [],
      surfacePageNumber: nextPageNumber,
      surfacePageCount: pageCount,
    });
    nextPageNumber += 1;
  }

  appendix.forEach((pageTables, idx) => {
    leaves.push({
      id: `${surface.surfaceId}#p${nextPageNumber + idx}`,
      type: "appendix",
      surface,
      layoutId: "L08.appendix",
      tables: pageTables,
      surfacePageNumber: nextPageNumber + idx,
      surfacePageCount: pageCount,
    });
  });

  return leaves;
}

/** Chunk decade groups into register pages by a row budget (groups kept whole). */
function packRegister(groups: ChronologyGroup[]): ChronologyGroup[][] {
  const pages: ChronologyGroup[][] = [];
  let page: ChronologyGroup[] = [];
  // First page also carries the folder title + scope; reserve room for it.
  let used = REGISTER_FIRST_RESERVE;
  for (const g of groups) {
    const w = g.surfaces.length + 1; // header + rows
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

  const leaves: Leaf[] = regPages.map((regGroups, idx) => ({
    id: `${folder.folderId}#register-${idx + 1}`,
    type: "register",
    folder,
    regGroups,
    regPageNumber: idx + 1,
    regPageCount: regPages.length,
  }));

  leaves.push({
    id: `${folder.folderId}#bookmark`,
    type: "bookmark",
    folder,
  });

  for (const surface of surfaces) {
    leaves.push(...paginateSurface(surface));
  }
  return leaves;
}

/** Map each surface id to the leaf index of its first (main) page. */
export function surfaceLeafIndex(leaves: Leaf[]): Map<string, number> {
  const map = new Map<string, number>();
  leaves.forEach((leaf, i) => {
    if (leaf.type === "main" && leaf.surface && !map.has(leaf.surface.surfaceId)) {
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
    if (leaf.type === "main" && leaf.surface) {
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
