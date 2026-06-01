import type { Surface, SurfaceTable } from "@/types/archive";

export type AppendixLayoutId =
  | "AX01.rights"
  | "AX02.citation"
  | "AX03.relations"
  | "AX04.context"
  | "AX05.statement"
  | "AX06.typed-index";

export const APPENDIX_LAYOUT_LABEL: Record<AppendixLayoutId, string> = {
  "AX01.rights": "Rights evidence",
  "AX02.citation": "Source citation register",
  "AX03.relations": "Relations classification",
  "AX04.context": "Protocol context packet",
  "AX05.statement": "Source statement",
  "AX06.typed-index": "Typed index",
};

export const APPENDIX_LAYOUT_PRIORITY: Record<AppendixLayoutId, number> = {
  "AX01.rights": 1,
  "AX02.citation": 1,
  "AX03.relations": 1,
  "AX04.context": 1,
  "AX05.statement": 1,
  "AX06.typed-index": 1 / 3,
};

export function appendixFrameClass(layoutId: AppendixLayoutId): string {
  switch (layoutId) {
    case "AX02.citation":
      return "leaf--appendix-landscape";
    case "AX03.relations":
    case "AX06.typed-index":
      return "leaf--appendix-square";
    case "AX01.rights":
    case "AX04.context":
    case "AX05.statement":
    default:
      return "leaf--appendix-vertical";
  }
}

export function fallbackAppendixLayout(
  surface?: Surface,
  evidenceTables: SurfaceTable[] = [],
): AppendixLayoutId {
  if (surface?.image.state === "IMG00" && hasKind(evidenceTables, "RIGHTS")) {
    return "AX01.rights";
  }
  return "AX05.statement";
}

export function resolveAppendixLayout(
  surface: Surface | undefined,
  evidenceTables: SurfaceTable[] = [],
  layoutId?: AppendixLayoutId,
): AppendixLayoutId {
  return layoutId ?? fallbackAppendixLayout(surface, evidenceTables);
}

function stableHash(value: string): number {
  let hash = 2166136261;
  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function hasKind(tables: SurfaceTable[], kind: SurfaceTable["kind"]): boolean {
  return tables.some((table) => table.kind === kind);
}

function rowCount(tables: SurfaceTable[]): number {
  return tables.reduce((total, table) => total + table.rows.length, 0);
}

export function selectAppendixLayout(
  surface: Surface,
  evidenceTables: SurfaceTable[],
  pageIndex = 0,
): AppendixLayoutId {
  const hash = stableHash(`${surface.surfaceId}:${pageIndex}`);
  const heavyIndexEligible = rowCount(surface.tables) >= 24 && hash % 3 === 0;

  if (hasKind(evidenceTables, "SOURCE")) {
    return heavyIndexEligible ? "AX06.typed-index" : "AX05.statement";
  }

  if (hasKind(evidenceTables, "CITATIONS")) {
    return "AX02.citation";
  }

  if (hasKind(evidenceTables, "RELATIONS") || hasKind(evidenceTables, "CLASSIFICATION")) {
    return heavyIndexEligible ? "AX06.typed-index" : "AX03.relations";
  }

  if (hasKind(evidenceTables, "RIGHTS")) {
    if (surface.image.state !== "IMG00") return "AX04.context";

    const img00Cycle: AppendixLayoutId[] = [
      "AX01.rights",
      "AX01.rights",
      "AX02.citation",
      "AX03.relations",
      "AX04.context",
      "AX05.statement",
    ];
    return img00Cycle[hash % img00Cycle.length];
  }

  return heavyIndexEligible ? "AX06.typed-index" : "AX05.statement";
}
