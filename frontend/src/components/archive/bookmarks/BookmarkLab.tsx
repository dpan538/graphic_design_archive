import type { Folder, FolderTypeKey, Surface, SurfaceFolderRef } from "@/types/archive";
import {
  getFolder,
  getFolderInk,
  getSurface,
  getSurfacesForFolder,
  sortChronologically,
} from "@/lib/archive-data";

type BookmarkTone = "bone" | "oat" | "fiber";

interface BookmarkBadge {
  type: FolderTypeKey;
  title: string;
}

interface BookmarkShellProps {
  children: React.ReactNode;
  className: string;
  tone: BookmarkTone;
  badges: BookmarkBadge[];
  label: string;
}

function mustSurface(id: string): Surface {
  const surface = getSurface(id);
  if (!surface) throw new Error(`Missing bookmark test surface: ${id}`);
  return surface;
}

function mustFolder(type: FolderTypeKey, slug: string): Folder {
  const folder = getFolder(type, slug);
  if (!folder) throw new Error(`Missing bookmark test folder: ${type}/${slug}`);
  return folder;
}

function clip(text: string, max = 84): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trim()}…`;
}

function spanLabel(start: number | null, end: number | null): string {
  if (start && end && start !== end) return `${start}–${end}`;
  if (start) return String(start);
  if (end) return String(end);
  return "date under review";
}

function badgesFromSurface(surface: Surface): BookmarkBadge[] {
  return surface.folders.map((folder) => ({
    type: folder.type,
    title: folder.title,
  }));
}

function BookmarkBadges({ badges }: { badges: BookmarkBadge[] }) {
  const visible = badges.slice(0, 3);
  const overflow = Math.max(0, badges.length - visible.length);
  return (
    <div className="bookmark-badges" aria-label={badges.map((b) => b.title).join(", ")}>
      {visible.map((badge, index) => (
        <span
          key={`${badge.type}-${badge.title}`}
          className="bookmark-badge"
          title={`${badge.type}: ${badge.title}`}
          style={{
            backgroundColor: getFolderInk(badge.type),
            zIndex: visible.length - index,
          }}
        >
          {badge.type.slice(0, 1).toUpperCase()}
        </span>
      ))}
      {overflow > 0 ? <span className="bookmark-badge-more">+{overflow}</span> : null}
    </div>
  );
}

function FolderLine({ folders }: { folders: SurfaceFolderRef[] }) {
  return (
    <p className="bookmark-folder-line">
      {folders.slice(0, 3).map((folder) => `${folder.type}: ${folder.title}`).join(" / ")}
    </p>
  );
}

function folderSamples(folder: Folder): Surface[] {
  return sortChronologically(getSurfacesForFolder(folder)).slice(0, 2);
}

function BookmarkShell({
  children,
  className,
  tone,
  badges,
  label,
}: BookmarkShellProps) {
  return (
    <article className={`bookmark ${className}`} data-tone={tone}>
      <BookmarkBadges badges={badges} />
      <span className="bookmark-template">{label}</span>
      {children}
    </article>
  );
}

function TallIndexBookmark({ surface }: { surface: Surface }) {
  return (
    <BookmarkShell
      className="bookmark--vertical bookmark--v-index"
      tone="bone"
      badges={badgesFromSurface(surface)}
      label="BM01 / tall index"
    >
      <header className="bookmark-title-stack">
        <p className="bookmark-kicker">Surface index</p>
        <h2>{clip(surface.title, 62)}</h2>
        <p>{surface.dateText}</p>
      </header>
      <div className="bookmark-rule" />
      <dl className="bookmark-spec">
        <dt>creator</dt>
        <dd>{clip(surface.creator, 36)}</dd>
        <dt>medium</dt>
        <dd>{clip(surface.medium, 36)}</dd>
        <dt>object</dt>
        <dd>{clip(surface.objectType, 36)}</dd>
        <dt>source</dt>
        <dd>{clip(surface.sourceName, 36)}</dd>
        <dt>access</dt>
        <dd>{surface.accessDate}</dd>
        <dt>score</dt>
        <dd>{surface.completenessScore} / {surface.rights.state}</dd>
      </dl>
      <div className="bookmark-spacer" />
      <FolderLine folders={surface.folders} />
      <footer>
        <span>{surface.provisionalDisplayNumber}</span>
        <span>{surface.image.state}</span>
      </footer>
    </BookmarkShell>
  );
}

function FolderRegisterBookmark({ folder }: { folder: Folder }) {
  const badges: BookmarkBadge[] = [{ type: folder.type, title: folder.title }];
  const samples = folderSamples(folder);
  return (
    <BookmarkShell
      className="bookmark--vertical bookmark--v-register"
      tone="oat"
      badges={badges}
      label="BM02 / folder register"
    >
      <header className="bookmark-centered">
        <p className="bookmark-kicker">{folder.type} folder</p>
        <h2>{folder.title}</h2>
      </header>
      <div className="bookmark-count">{String(folder.surfaceIds.length).padStart(3, "0")}</div>
      <p className="bookmark-large-note">{spanLabel(folder.dateStart, folder.dateEnd)}</p>
      <div className="bookmark-rule" />
      <p className="bookmark-small-text">{clip(folder.scopeNote, 92)}</p>
      <ol className="bookmark-mini-list">
        {samples.map((surface) => (
          <li key={surface.surfaceId}>
            <span>{surface.dateText}</span>
            {clip(surface.title, 34)}
          </li>
        ))}
      </ol>
      <div className="bookmark-spacer" />
      <footer>
        <span>{folder.folderId}</span>
        <span>{folder.slug}</span>
      </footer>
    </BookmarkShell>
  );
}

function ReviewBookmark({ surface }: { surface: Surface }) {
  return (
    <BookmarkShell
      className="bookmark--vertical bookmark--v-review"
      tone="fiber"
      badges={badgesFromSurface(surface)}
      label="BM03 / review card"
    >
      <header>
        <p className="bookmark-kicker">Promotion check</p>
        <h2>{clip(surface.title, 52)}</h2>
      </header>
      <div className="bookmark-review-grid">
        <span>score</span>
        <strong>{surface.completenessScore}</strong>
        <span>image</span>
        <strong>{surface.image.state}</strong>
        <span>rights</span>
        <strong>{surface.reviewGates.rightsReviewed ? "yes" : "hold"}</strong>
        <span>date</span>
        <strong>{surface.reviewGates.dateKnown ? "yes" : "hold"}</strong>
        <span>class</span>
        <strong>{surface.reviewGates.classificationKnown ? "yes" : "hold"}</strong>
        <span>source</span>
        <strong>{surface.reviewGates.sourceUrl ? "yes" : "hold"}</strong>
      </div>
      <p className="bookmark-vertical-note">{clip(surface.rights.label, 80)}</p>
      <dl className="bookmark-spec bookmark-spec--compact">
        <dt>creator</dt>
        <dd>{clip(surface.creator, 32)}</dd>
        <dt>source</dt>
        <dd>{clip(surface.sourceName, 32)}</dd>
        <dt>medium</dt>
        <dd>{clip(surface.medium, 32)}</dd>
      </dl>
      <div className="bookmark-spacer" />
      <p className="bookmark-small-text">{clip(surface.sourceName, 70)}</p>
      <footer>
        <span>{surface.surfaceType}</span>
        <span>{surface.dateText}</span>
      </footer>
    </BookmarkShell>
  );
}

function CitationSlip({ surface }: { surface: Surface }) {
  return (
    <BookmarkShell
      className="bookmark--horizontal bookmark--h-citation"
      tone="bone"
      badges={badgesFromSurface(surface)}
      label="BM04 / citation slip"
    >
      <div className="bookmark-horizontal-main">
        <p className="bookmark-kicker">Citation marker</p>
        <h2>{clip(surface.title, 76)}</h2>
        <p>{clip(surface.sourceName, 58)} / accessed {surface.accessDate}</p>
      </div>
      <div className="bookmark-horizontal-side">
        <span>{surface.dateText}</span>
        <strong>{surface.seqLabel}</strong>
      </div>
    </BookmarkShell>
  );
}

function ChronologySlip({ folder }: { folder: Folder }) {
  const badges: BookmarkBadge[] = [{ type: folder.type, title: folder.title }];
  return (
    <BookmarkShell
      className="bookmark--horizontal bookmark--h-chrono"
      tone="oat"
      badges={badges}
      label="BM05 / chronology slip"
    >
      <div className="bookmark-horizontal-main">
        <p className="bookmark-kicker">Chronology jump</p>
        <h2>{folder.title}</h2>
        <p>{clip(folder.scopeNote, 104)}</p>
      </div>
      <div className="bookmark-years">
        <span>{spanLabel(folder.dateStart, folder.dateEnd)}</span>
        <strong>{folder.surfaceIds.length} surfaces</strong>
      </div>
    </BookmarkShell>
  );
}

function PoeticSlip({ surface }: { surface: Surface }) {
  return (
    <BookmarkShell
      className="bookmark--horizontal bookmark--h-poetic"
      tone="fiber"
      badges={badgesFromSurface(surface)}
      label="BM06 / sparse poetic"
    >
      <p className="bookmark-poem">
        {surface.objectType || "graphic record"}
        <span>{surface.dateText}</span>
        {surface.placeText || surface.sourceName}
      </p>
      <h2>{clip(surface.title, 48)}</h2>
      <p className="bookmark-microline">
        {surface.folders.slice(0, 2).map((folder) => folder.title).join(" / ")}
      </p>
    </BookmarkShell>
  );
}

export default function BookmarkLab({
  mode = "all",
}: {
  mode?: "all" | "vertical" | "horizontal";
}) {
  const typographicBook = mustSurface("SURF-GAX1970R002");
  const travelFolder = mustFolder("theme", "travel-and-transport-poster-culture");
  const modernPoster = mustSurface("SURF-ER1830R052");
  const ascotPoster = mustSurface("SURF-ER1830R073");
  const franceFolder = mustFolder("region", "france");
  const kissPoster = mustSurface("SURF-MC1930R056");

  return (
    <main className="bookmark-lab" data-mode={mode}>
      {mode !== "horizontal" ? (
        <section className="bookmark-lab__set bookmark-lab__set--vertical" aria-label="Vertical bookmark layouts">
          <TallIndexBookmark surface={typographicBook} />
          <FolderRegisterBookmark folder={travelFolder} />
          <ReviewBookmark surface={modernPoster} />
        </section>
      ) : null}
      {mode !== "vertical" ? (
        <section className="bookmark-lab__set bookmark-lab__set--horizontal" aria-label="Horizontal bookmark layouts">
          <CitationSlip surface={ascotPoster} />
          <ChronologySlip folder={franceFolder} />
          <PoeticSlip surface={kissPoster} />
        </section>
      ) : null}
    </main>
  );
}
