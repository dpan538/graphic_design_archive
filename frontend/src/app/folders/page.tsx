import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { CountsCard } from "@/components/archive/shell/sidebar";
import FolderDrawer, {
  type DrawerItem,
} from "@/components/archive/drawer/FolderDrawer";
import { getFolderTypeSummaries } from "@/lib/archive-data";
import { getFolderInk } from "@/lib/archive-data";

export const metadata = { title: "Folder types — Archive Box" };

export default function FolderTypesPage() {
  const items: DrawerItem[] = getFolderTypeSummaries().map(
    ({ folderType, folderCount, surfaceCount }) => ({
      key: folderType.type,
      type: folderType.type,
      ink: getFolderInk(folderType.type),
      tabLabel: folderType.label,
      title: folderType.label,
      href: `/folders/${folderType.type}`,
      reveal: [
        folderType.scopeNote,
        `${folderCount} folders · ${surfaceCount.toLocaleString("en-US")} design records`,
      ],
    }),
  );

  return (
    <ArchiveShell
      activeNav="folders"
      main={<FolderDrawer items={items} />}
      cornerCard={<CountsCard />}
    />
  );
}
