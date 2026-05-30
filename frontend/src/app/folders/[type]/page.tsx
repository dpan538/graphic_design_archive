import { notFound } from "next/navigation";
import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import FolderDrawer, {
  type DrawerItem,
} from "@/components/archive/drawer/FolderDrawer";
import {
  allFolderTypeParams,
  dateSpanLabel,
  getFolderInk,
  getFoldersByType,
  getFolderType,
  getSurfacesForFolder,
  isFolderTypeKey,
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

  const items: DrawerItem[] = getFoldersByType(folderType.type).map(
    (folder) => {
      const surfaces = getSurfacesForFolder(folder);
      const mix = surfaceMix(surfaces);
      return {
        key: folder.folderId,
        type: folder.type,
        ink: getFolderInk(folder.type),
        tabLabel: folderType.label,
        title: folder.title,
        href: `/folders/${folder.type}/${folder.slug}`,
        reveal: [
          dateSpanLabel(folder.dateStart, folder.dateEnd),
          folder.scopeNote,
          `${surfaces.length} members · ${mix.sheet} sheet · ${mix.card} card · ${mix.fallback_stub} stub`,
        ],
      };
    },
  );

  return (
    <ArchiveShell
      activeNav="folders"
      folderInk={getFolderInk(folderType.type)}
      main={<FolderDrawer items={items} />}
    />
  );
}
