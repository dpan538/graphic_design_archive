import { notFound } from "next/navigation";
import Reader from "@/components/archive/reader/Reader";
import { LAYOUT_LABEL } from "@/lib/layout";
import {
  getFolderById,
  getFolderInk,
  getFolderType,
  getSurface,
} from "@/lib/archive-data";
import { paginateSurface, type JumpTarget } from "@/lib/paginate";

// The archive currently exposes 8,636 reading routes. Rendering the selected
// record on demand keeps those stable URLs without rebuilding every object for
// each interface-only release. The application already requires a server for
// its evidence routes, so this does not remove an existing static-only target.
export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const s = getSurface(id);
  return { title: s ? `${s.title} — Archive Box` : "Surface" };
}

export default async function SurfaceReaderPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ folder?: string }>;
}) {
  const { id } = await params;
  const { folder: folderParam } = await searchParams;
  const surface = getSurface(id);
  if (!surface) notFound();

  // Reading-folder context: explicit ?folder=, else first membership.
  const activeFolder =
    (folderParam ? getFolderById(folderParam) : undefined) ??
    (surface.folders[0] ? getFolderById(surface.folders[0].folderId) : undefined);

  const leaves = paginateSurface(surface);
  const jumpTargets: JumpTarget[] = leaves.map((leaf, i) => ({
    leafIndex: i,
    label: `Page ${leaf.surfacePageNumber}`,
    sublabel: leaf.layoutId ? LAYOUT_LABEL[leaf.layoutId] : "",
    surfaceId: surface.surfaceId,
  }));

  const ink = activeFolder ? getFolderInk(activeFolder.type) : "#2E2925";
  const subtitle = activeFolder
    ? `${getFolderType(activeFolder.type)?.label ?? activeFolder.type} · ${activeFolder.title}`
    : "Standalone surface";

  return (
    <Reader
      leaves={leaves}
      jumpTargets={jumpTargets}
      activeFolderId={activeFolder?.folderId}
      folderInk={ink}
      folderType={activeFolder?.type}
      contextTitle={surface.title}
      contextSubtitle={subtitle}
      backHref={
        activeFolder
          ? `/folders/${activeFolder.type}/${activeFolder.slug}`
          : "/folders"
      }
      backLabel={activeFolder ? activeFolder.title : "Folders"}
    />
  );
}
