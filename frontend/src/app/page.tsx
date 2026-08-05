import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import FolderDrawer, {
  type DrawerItem,
} from "@/components/archive/drawer/FolderDrawer";
import { getGlobalCounts, getFolderTypeSummaries } from "@/lib/archive-data";

function HomeArchiveBox() {
  const counts = getGlobalCounts();
  return (
    <details className="home-archive-summary">
      <summary>
        <span>Archive counts</span>
        <strong>{counts.surfaces.toLocaleString("en-US")}</strong>
        <small>surfaces</small>
      </summary>
      <dl>
        <div>
          <dt>folders</dt>
          <dd>{counts.folders}</dd>
        </div>
        <div>
          <dt>surfaces</dt>
          <dd>{counts.surfaces.toLocaleString("en-US")}</dd>
        </div>
        <div>
          <dt>images</dt>
          <dd>{counts.imageCoveragePercent}%</dd>
        </div>
      </dl>
    </details>
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
