import type { Folder } from "@/types/archive";

export type ReadingNoteLayoutId =
  | "RN01.stack"
  | "RN02.pair-strip"
  | "RN03.sparse-strip"
  | "RN04.ledger";

export const READING_NOTE_LAYOUTS: Record<
  ReadingNoteLayoutId,
  { label: string; priority: "standard" | "support" | "sparse" }
> = {
  "RN01.stack": {
    label: "Stacked 3:4 note pair",
    priority: "standard",
  },
  "RN02.pair-strip": {
    label: "Joined 1:3 strip pair",
    priority: "support",
  },
  "RN03.sparse-strip": {
    label: "Single sparse 1:3 strip",
    priority: "sparse",
  },
  "RN04.ledger": {
    label: "Upright reading ledger",
    priority: "standard",
  },
};

export function selectReadingNoteLayout(folder: Folder): ReadingNoteLayoutId {
  if (folder.surfaceIds.length <= 2) return "RN03.sparse-strip";
  if (folder.type === "region") return "RN01.stack";
  if (folder.type === "theme") return "RN02.pair-strip";
  return "RN04.ledger";
}

export function readingNoteFrameClass(layoutId: ReadingNoteLayoutId): string {
  switch (layoutId) {
    case "RN01.stack":
      return "leaf--reading-note-stack";
    case "RN02.pair-strip":
      return "leaf--reading-note-pair-strip";
    case "RN03.sparse-strip":
      return "leaf--reading-note-sparse-strip";
    case "RN04.ledger":
    default:
      return "leaf--reading-note-ledger";
  }
}
