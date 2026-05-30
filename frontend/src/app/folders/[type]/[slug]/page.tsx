import { notFound } from "next/navigation";
import Reader from "@/components/archive/reader/Reader";
import {
  allFolderParams,
  getFolder,
  getFolderInk,
  getFolderType,
  isFolderTypeKey,
} from "@/lib/archive-data";
import { folderJumpTargets, paginateFolder } from "@/lib/paginate";

export function generateStaticParams() {
  return allFolderParams();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ type: string; slug: string }>;
}) {
  const { type, slug } = await params;
  const folder = getFolder(type, slug);
  return { title: folder ? `${folder.title} — Archive Box` : "Folder" };
}

export default async function FolderReaderPage({
  params,
}: {
  params: Promise<{ type: string; slug: string }>;
}) {
  const { type, slug } = await params;
  if (!isFolderTypeKey(type)) notFound();
  const folder = getFolder(type, slug);
  if (!folder) notFound();

  const leaves = paginateFolder(folder);
  const jumpTargets = folderJumpTargets(leaves);
  const folderTypeLabel = getFolderType(type)?.label ?? type;

  return (
    <Reader
      leaves={leaves}
      jumpTargets={jumpTargets}
      activeFolderId={folder.folderId}
      folderInk={getFolderInk(type)}
      folderType={folder.type}
      contextTitle={folder.title}
      contextSubtitle={`${folderTypeLabel} folder`}
      backHref={`/folders/${type}`}
      backLabel={`${folderTypeLabel} folders`}
    />
  );
}
