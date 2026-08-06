import ArchiveShell from "@/components/archive/shell/ArchiveShell";
import FolderDrawer, {
  type DrawerItem,
} from "@/components/archive/drawer/FolderDrawer";
import { getFolderTypeSummaries } from "@/lib/archive-data";
import traceAtlas from "../../public/data/trace-v48/atlas.json";

function HomeArchiveBox() {
  return (
    <details className="home-archive-summary">
      <summary>
        <span>Archive objects</span>
        <strong>{traceAtlas.counts.activeObjects.toLocaleString("en-US")}</strong>
        <small>active, source-linked records</small>
      </summary>
      <dl>
        <div>
          <dt>active objects</dt>
          <dd>{traceAtlas.counts.activeObjects.toLocaleString("en-US")}</dd>
        </div>
        <div>
          <dt>TRACE relations</dt>
          <dd>{traceAtlas.counts.traceEdges.toLocaleString("en-US")}</dd>
        </div>
        <div>
          <dt>research trees</dt>
          <dd>{traceAtlas.counts.activeTrees}</dd>
        </div>
      </dl>
    </details>
  );
}

export default function HomePage() {
  const items: DrawerItem[] = getFolderTypeSummaries().map(
    ({ folderType, folderCount }) => ({
      key: folderType.type,
      type: folderType.type,
      tabLabel: folderType.label,
      title: folderType.label,
      href: `/folders/${folderType.type}`,
      reveal: [
        folderType.scopeNote,
        folderType.type === "region"
          ? `${Math.max(0, folderCount - 1)} active research folders · 1 review route isolated`
          : `${folderCount} research folders`,
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
