import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import FolderDrawer, {
  type DrawerItem,
} from "@/components/archive/drawer/FolderDrawer";
import { getGlobalCounts, getFolderTypeSummaries } from "@/lib/archive-data";

function HomeArchiveBox() {
  const counts = getGlobalCounts();
  return (
    <div className="home-archive-summary" aria-label="Archive totals">
      <span><strong>{counts.folders}</strong> folders</span>
      <span><strong>{counts.surfaces}</strong> surfaces</span>
      <span><strong>{counts.imageCoveragePercent}%</strong> images</span>
    </div>
  );
}

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
      cornerCard={<HomeArchiveBox />}
    />
  );
}
