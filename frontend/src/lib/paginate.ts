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
  type: "register" | "main" | "appendix";
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

/** Greedily pack tables: first the main leaf, then appendix leaves. */
function packTables(
  tables: SurfaceTable[],
  mainBudget: number,
): { main: SurfaceTable[]; appendix: SurfaceTable[][] } {
  const main: SurfaceTable[] = [];
  let used = 0;
  let i = 0;
  // A zero budget means the layout's first leaf is text-only (no tables).
  if (mainBudget > 0) {
    for (; i < tables.length; i++) {
      const w = tableWeight(tables[i]);
      if (main.length > 0 && used + w > mainBudget) break;
      main.push(tables[i]);
      used += w;
    }
  }

  const appendix: SurfaceTable[][] = [];
  let page: SurfaceTable[] = [];
  let pageUsed = 0;
  for (; i < tables.length; i++) {
    const w = tableWeight(tables[i]);
    if (page.length > 0 && pageUsed + w > APPENDIX_BUDGET) {
      appendix.push(page);
      page = [];
      pageUsed = 0;
    }
    page.push(tables[i]);
    pageUsed += w;
  }
  if (page.length > 0) appendix.push(page);

  return { main, appendix };
}

/** Build the leaf sequence for a single surface (no folder register). */
export function paginateSurface(surface: Surface): Leaf[] {
  const layoutId = selectLayout(surface);
  const variant = sheetVariant(surface);
  const tables = orderedTables(surface);
  const { main, appendix } = packTables(tables, mainTableBudget(layoutId));

  const pageCount = 1 + appendix.length;
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

  appendix.forEach((pageTables, idx) => {
    leaves.push({
      id: `${surface.surfaceId}#p${idx + 2}`,
      type: "appendix",
      surface,
      layoutId: "L08.appendix",
      tables: pageTables,
      surfacePageNumber: idx + 2,
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
