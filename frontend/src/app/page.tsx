import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { CountsCard } from "@/components/archive/shell/sidebar";
import FolderDrawer, {
  type DrawerItem,
} from "@/components/archive/drawer/FolderDrawer";
import { getFolderTypeSummaries } from "@/lib/archive-data";

export default function HomePage() {
  const items: DrawerItem[] = getFolderTypeSummaries().map(
    ({ folderType, folderCount, surfaceCount }) => ({
      key: folderType.type,
      type: folderType.type,
      tabLabel: folderType.label,
      title: folderType.label,
      href: `/folders/${folderType.type}`,
      reveal: [
        folderType.scopeNote,
        `${folderCount} folders · ${surfaceCount} surfaces`,
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
