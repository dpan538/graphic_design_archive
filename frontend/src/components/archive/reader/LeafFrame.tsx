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
import {
  selectTextPageLayout,
  textPageFrameClass,
} from "@/lib/text-page-layout";
import { renderLeafContent, type LeafCtx } from "../layouts";

/**
 * Physical frame around one leaf. The only fixed chrome drawn here is the
 * folder-colour bar on the left edge; the accession number now lives in the
 * leaf header band (see LeafHead) so it never overlaps the content.
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
    <div className={`leaf ${sizeClass} ${single ? "leaf--single" : ""}`}>
      <span className="folder-color-bar" aria-hidden />
      {renderLeafContent(leaf, activeFolderId, ctx)}
    </div>
  );
}
