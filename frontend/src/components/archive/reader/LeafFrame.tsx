import type { Leaf } from "@/lib/paginate";
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
  return (
    <div className={`leaf ${single ? "leaf--single" : ""}`}>
      <span className="folder-color-bar" aria-hidden />
      {renderLeafContent(leaf, activeFolderId, ctx)}
    </div>
  );
}
