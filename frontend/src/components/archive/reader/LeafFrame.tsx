import type { Leaf } from "@/lib/paginate";
import { appendixFrameClass, resolveAppendixLayout } from "@/lib/appendix-layout";
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
      : leaf.type === "appendix"
      ? `leaf--appendix ${appendixFrameClass(
          resolveAppendixLayout(leaf.surface, leaf.tables ?? [], leaf.appendixLayoutId),
        )}`
      : leaf.layoutId === "L06.card"
        ? "leaf--card"
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
