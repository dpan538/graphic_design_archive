import type { Leaf } from "@/lib/paginate";
import { appendixFrameClass, resolveAppendixLayout } from "@/lib/appendix-layout";
import {
  archiveCardFrameClass,
} from "@/lib/card-asset-layout";
import {
  readingNoteFrameClass,
  selectReadingNoteLayout,
} from "@/lib/reading-note-layout";
import { sourceSlipFrameClass } from "@/lib/slip-layout";
import { subSheetFrameClass } from "@/lib/sub-sheet-layout";
import {
  selectTextPageLayout,
  textPageFrameClass,
} from "@/lib/text-page-layout";
import {
  layoutContractDataAttrs,
  layoutContractForLeaf,
} from "@/lib/layout-contracts";
import { renderLeafContent, type LeafCtx } from "../layouts";

/**
 * Physical frame around one leaf. Folder colour now belongs to local labels,
 * tabs, badges, and navigation context; the printable leaf itself must not
 * carry a legacy left-edge colour rail.
 */
export default function LeafFrame({
  leaf,
  single,
  activeFolderId,
  ctx,
}: {
  leaf: Leaf;
  single: boolean;
  activeFolderId?: string;
  ctx?: LeafCtx;
}) {
  const contract = layoutContractForLeaf(leaf);
  const sizeClass =
    leaf.type === "bookmark"
      ? "leaf--bookmark"
      : leaf.type === "reading_note"
      ? `leaf--reading-note ${readingNoteFrameClass(
            leaf.readingNoteLayoutId ??
              (leaf.folder ? selectReadingNoteLayout(leaf.folder) : "RN04.ledger"),
          )}`
      : leaf.type === "text"
        ? textPageFrameClass(
            leaf.textPageLayoutId ??
              (leaf.surface ? selectTextPageLayout(leaf.surface) : "TP06.spread-cover"),
          )
      : leaf.type === "subsheet"
        ? `leaf--sub-sheet ${subSheetFrameClass(leaf.subSheetLayoutId ?? "SS01.schedule-index")}`
      : leaf.type === "slip"
        ? `leaf--slip ${sourceSlipFrameClass(leaf.slipLayoutId ?? "SLIP02.portrait")}`
      : leaf.type === "appendix"
      ? `leaf--appendix ${appendixFrameClass(
          resolveAppendixLayout(leaf.surface, leaf.tables ?? [], leaf.appendixLayoutId),
        )}`
      : leaf.layoutId === "L06.card"
        ? `leaf--card ${archiveCardFrameClass(leaf.cardLayoutId ?? "CARD02.typography-portrait")}`
        : leaf.layoutId === "L07.stub"
          ? "leaf--stub"
          : "leaf--sheet";
  return (
    <div
      className={`leaf ${sizeClass} ${single ? "leaf--single" : ""}`}
      data-leaf-type={leaf.type}
      data-layout-id={leaf.layoutId}
      data-image-state={leaf.surface?.image.state}
      {...layoutContractDataAttrs(contract)}
    >
      {renderLeafContent(leaf, activeFolderId, ctx)}
    </div>
  );
}
