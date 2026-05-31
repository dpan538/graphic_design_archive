import type { Folder, FolderTypeKey, Surface, SurfaceFolderRef } from "@/types/archive";
import {
  getFolder,
  getFolderInk,
  getSurface,
  getSurfacesForFolder,
  sortChronologically,
} from "@/lib/archive-data";

type CardMode = "all" | "square" | "rectangle";
type CardTone = "white" | "blue" | "orange" | "green" | "paper";

interface CardBadge {
  type: FolderTypeKey;
  title: string;
}

interface CardShellProps {
  children: React.ReactNode;
  className: string;
  tone: CardTone;
  badges: CardBadge[];
  label: string;
}

function mustSurface(id: string): Surface {
  const surface = getSurface(id);
  if (!surface) throw new Error(`Missing card test surface: ${id}`);
  return surface;
}

function mustFolder(type: FolderTypeKey, slug: string): Folder {
  const folder = getFolder(type, slug);
  if (!folder) throw new Error(`Missing card test folder: ${type}/${slug}`);
  return folder;
}

function clip(text: string, max = 78): string {
  if (!text) return "unrecorded";
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trim()}…`;
}

function spanLabel(start: number | null, end: number | null): string {
  if (start && end && start !== end) return `${start}–${end}`;
  if (start) return String(start);
  if (end) return String(end);
  return "date under review";
}

function badgesFromSurface(surface: Surface): CardBadge[] {
  return surface.folders.map((folder) => ({
    type: folder.type,
    title: folder.title,
  }));
}

function CardBadges({ badges }: { badges: CardBadge[] }) {
  const visible = badges.slice(0, 3);
  return (
    <div className="card-badges" aria-label={badges.map((b) => b.title).join(", ")}>
      {visible.map((badge, index) => (
        <span
          key={`${badge.type}-${badge.title}`}
          className="card-badge"
          title={`${badge.type}: ${badge.title}`}
          style={{
            backgroundColor: getFolderInk(badge.type),
            zIndex: visible.length - index,
          }}
        >
          {badge.type.slice(0, 1).toUpperCase()}
        </span>
      ))}
    </div>
  );
}

function CardShell({ children, className, tone, badges, label }: CardShellProps) {
  return (
    <article className={`asset-card ${className}`} data-tone={tone}>
      <CardBadges badges={badges} />
      <span className="asset-card__label">{label}</span>
      {children}
    </article>
  );
}

function MiniFolders({ folders }: { folders: SurfaceFolderRef[] }) {
  return (
    <p className="asset-card__folders">
      {folders.slice(0, 3).map((folder) => `${folder.type}: ${folder.title}`).join(" / ")}
    </p>
  );
}

function ObjectMark({ surface }: { surface: Surface }) {
  return (
    <div className="object-mark" aria-label={surface.image.state}>
      <span className="object-mark__bar" />
      <span className="object-mark__dot object-mark__dot--a" />
      <span className="object-mark__dot object-mark__dot--b" />
      <span className="object-mark__dot object-mark__dot--c" />
      <strong>{surface.image.state}</strong>
    </div>
  );
}

function TypeCloud({ surface }: { surface: Surface }) {
  const source = `${surface.title} ${surface.dateText} ${surface.sourceRecordId}`
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "");
  const glyphs = Array.from({ length: 44 }, (_, i) => source[i % source.length] ?? "0");
  return (
    <div className="type-cloud" aria-hidden>
      {glyphs.map((glyph, index) => (
        <span
          key={`${glyph}-${index}`}
          style={
            {
              "--x": `${(index * 19) % 92}%`,
              "--y": `${(index * 31) % 88}%`,
              "--r": `${((index % 9) - 4) * 8}deg`,
            } as React.CSSProperties
          }
        >
          {glyph}
        </span>
      ))}
    </div>
  );
}

function folderSamples(folder: Folder, max = 4): Surface[] {
  return sortChronologically(getSurfacesForFolder(folder)).slice(0, max);
}

function ObjectSquareCard({ surface }: { surface: Surface }) {
  return (
    <CardShell
      className="asset-card--square card-object-square"
      tone="white"
      badges={badgesFromSurface(surface)}
      label="object / square"
    >
      <header>
        <p>Object display</p>
        <h2>{clip(surface.title, 52)}</h2>
      </header>
      <ObjectMark surface={surface} />
      <dl>
        <dt>date</dt>
        <dd>{surface.dateText}</dd>
        <dt>medium</dt>
        <dd>{clip(surface.medium, 44)}</dd>
        <dt>source</dt>
        <dd>{clip(surface.sourceName, 34)}</dd>
      </dl>
    </CardShell>
  );
}

function ObjectRectCard({ surface }: { surface: Surface }) {
  return (
    <CardShell
      className="asset-card--rectangle card-object-rect"
      tone="paper"
      badges={badgesFromSurface(surface)}
      label="object / rectangle"
    >
      <div className="card-object-rect__plate">
        <ObjectMark surface={surface} />
      </div>
      <div className="card-object-rect__text">
        <p>source object</p>
        <h2>{surface.title}</h2>
        <span>{surface.dateText}</span>
        <MiniFolders folders={surface.folders} />
      </div>
    </CardShell>
  );
}

function PostcardSquare({ surface }: { surface: Surface }) {
  return (
    <CardShell
      className="asset-card--square card-postcard-square"
      tone="orange"
      badges={badgesFromSurface(surface)}
      label="postcard / square"
    >
      <div className="postcard-image-frame">
        <span>{surface.image.state}</span>
      </div>
      <h2>{clip(surface.title, 54)}</h2>
      <p>{clip(surface.creator, 56)}</p>
      <footer>{surface.dateText}</footer>
    </CardShell>
  );
}

function PostcardRect({ surface }: { surface: Surface }) {
  return (
    <CardShell
      className="asset-card--rectangle card-postcard-rect"
      tone="white"
      badges={badgesFromSurface(surface)}
      label="postcard / rectangle"
    >
      <div className="postcard-rect__title">
        <h2>{clip(surface.title, 42)}</h2>
        <p>{surface.dateText}</p>
      </div>
      <div className="postcard-rect__image" />
      <div className="postcard-rect__meta">
        <p>{clip(surface.creator, 64)}</p>
        <span>{clip(surface.medium, 42)}</span>
      </div>
    </CardShell>
  );
}

function TypeSquare({ surface }: { surface: Surface }) {
  return (
    <CardShell
      className="asset-card--square card-type-square"
      tone="green"
      badges={badgesFromSurface(surface)}
      label="type graphic / square"
    >
      <TypeCloud surface={surface} />
      <div className="type-square__copy">
        <h2>{clip(surface.title, 48)}</h2>
        <p>{surface.dateText} / {surface.image.state}</p>
      </div>
    </CardShell>
  );
}

function TypeRect({ surface }: { surface: Surface }) {
  return (
    <CardShell
      className="asset-card--rectangle card-type-rect"
      tone="blue"
      badges={badgesFromSurface(surface)}
      label="type graphic / rectangle"
    >
      <div className="type-rect__matrix" aria-hidden>
        <span>GRAPHIC</span>
        <span>DESIGN</span>
        <span>LETTERING</span>
        <span>TYPOGRAPHY</span>
      </div>
      <div className="type-rect__copy">
        <h2>{clip(surface.title, 74)}</h2>
        <p>{surface.creator}</p>
        <strong>{surface.dateText.slice(0, 4)}</strong>
      </div>
    </CardShell>
  );
}

function CollectionSquare({ folder }: { folder: Folder }) {
  const samples = folderSamples(folder, 3);
  return (
    <CardShell
      className="asset-card--square card-collection-square"
      tone="blue"
      badges={[{ type: folder.type, title: folder.title }]}
      label="collection / square"
    >
      <h2>{folder.title}</h2>
      <p>{spanLabel(folder.dateStart, folder.dateEnd)}</p>
      <strong>{folder.surfaceIds.length}</strong>
      <ol>
        {samples.map((surface) => (
          <li key={surface.surfaceId}>{clip(surface.title, 36)}</li>
        ))}
      </ol>
    </CardShell>
  );
}

function CollectionRect({ folder }: { folder: Folder }) {
  const samples = folderSamples(folder, 4);
  return (
    <CardShell
      className="asset-card--rectangle card-collection-rect"
      tone="green"
      badges={[{ type: folder.type, title: folder.title }]}
      label="collection / rectangle"
    >
      <div className="collection-rect__head">
        <p>{folder.type} folder</p>
        <h2>{folder.title}</h2>
        <span>{spanLabel(folder.dateStart, folder.dateEnd)}</span>
      </div>
      <ol>
        {samples.map((surface) => (
          <li key={surface.surfaceId}>
            <span>{surface.dateText}</span>
            {clip(surface.title, 46)}
          </li>
        ))}
      </ol>
      <strong>{folder.surfaceIds.length} surfaces</strong>
    </CardShell>
  );
}

export default function CardLab({ mode = "all" }: { mode?: CardMode }) {
  const specimen = mustSurface("SURF-GAX1970R006");
  const ascot = mustSurface("SURF-ER1830R073");
  const kiss = mustSurface("SURF-MC1930R056");
  const dwan = mustSurface("SURF-MC1930R077");
  const graphicDesign = mustSurface("SURF-MX1970R027");
  const france = mustFolder("region", "france");
  const travel = mustFolder("theme", "travel-and-transport-poster-culture");

  return (
    <main className="card-lab" data-mode={mode}>
      {mode !== "rectangle" ? (
        <section className="card-lab__set card-lab__set--square" aria-label="Square card layouts">
          <ObjectSquareCard surface={specimen} />
          <PostcardSquare surface={kiss} />
          <TypeSquare surface={specimen} />
          <CollectionSquare folder={france} />
        </section>
      ) : null}
      {mode !== "square" ? (
        <section className="card-lab__set card-lab__set--rectangle" aria-label="Rectangle card layouts">
          <ObjectRectCard surface={ascot} />
          <PostcardRect surface={dwan} />
          <TypeRect surface={graphicDesign} />
          <CollectionRect folder={travel} />
        </section>
      ) : null}
    </main>
  );
}
