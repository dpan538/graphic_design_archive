import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import { CountsCard } from "@/components/archive/shell/sidebar";
import FolderDrawer, {
  type DrawerItem,
} from "@/components/archive/drawer/FolderDrawer";
import { getGlobalCounts, getFolderTypeSummaries } from "@/lib/archive-data";

function HomeArchiveBox() {
  const counts = getGlobalCounts();
  return (
    <div className="home-archive-box">
      <CountsCard />
      <div className="home-archive-note">
        <p className="label-caps">Archive Box</p>
        <p>
          Four primary drawers organize the index. Region opens wider because
          geography carries the broadest local source distribution.
        </p>
      </div>
      <div className="home-archive-strip">
        <span>IMG {counts.imageCoveragePercent}%</span>
        <span>{counts.sources} sources</span>
      </div>
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
