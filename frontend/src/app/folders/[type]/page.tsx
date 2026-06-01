import { notFound } from "next/navigation";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import FolderTypeSpeedIndex, {
  type FolderTypeSpeedItem,
} from "@/components/archive/drawer/FolderTypeSpeedIndex";
import {
  allFolderTypeParams,
  dateSpanLabel,
  getFolderInk,
  getFoldersByType,
  getFolderType,
  getSurfacesForFolder,
  isFolderTypeKey,
  regionGroupLabel,
  surfaceMix,
} from "@/lib/archive-data";

export function generateStaticParams() {
  return allFolderTypeParams();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ type: string }>;
}) {
  const { type } = await params;
  const ft = getFolderType(type);
  return { title: ft ? `${ft.label} folders — Archive Box` : "Folders" };
}

export default async function FolderTypePage({
  params,
}: {
  params: Promise<{ type: string }>;
}) {
  const { type } = await params;
  if (!isFolderTypeKey(type)) notFound();
  const folderType = getFolderType(type);
  if (!folderType) notFound();

  const items: FolderTypeSpeedItem[] = getFoldersByType(folderType.type).map(
    (folder) => {
      const surfaces = getSurfacesForFolder(folder);
      const mix = surfaceMix(surfaces);
      return {
        key: folder.folderId,
        type: folder.type,
        groupLabel: folder.type === "region" ? regionGroupLabel(folder) : undefined,
        code: folder.title
          .replace(/[^a-z0-9 ]/gi, " ")
          .trim()
          .split(/\s+/)
          .slice(0, 2)
          .map((part) => part.slice(0, 3))
          .join("")
          .slice(0, 6)
          .toUpperCase(),
        title: folder.title,
        href: `/folders/${folder.type}/${folder.slug}`,
        count: surfaces.length,
        date: dateSpanLabel(folder.dateStart, folder.dateEnd),
        mix: `${mix.sheet} sheet · ${mix.card} card · ${mix.fallback_stub} stub`,
      };
    },
  );

  return (
    <ArchiveShell
      activeNav="folders"
      folderInk={getFolderInk(folderType.type)}
      main={<FolderTypeSpeedIndex folderType={folderType} items={items} />}
    />
  );
}
