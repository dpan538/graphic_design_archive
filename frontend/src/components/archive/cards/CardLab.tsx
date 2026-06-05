import type { Folder, FolderTypeKey, Surface, SurfaceFolderRef, SurfaceTable } from "@/types/archive";
import {
  getFolder,
  getFolderInk,
  getSurface,
  getSurfacesForFolder,
  sortChronologically,
} from "@/lib/archive-data";
import { isRenderableImage } from "@/lib/layout";
import {
  type ArchiveCardLayoutId,
  selectArchiveCardLayout,
} from "@/lib/card-asset-layout";

type CardMode = "all" | "square" | "rectangle" | "color" | "special" | "dense";

interface CardBadge {
  type: FolderTypeKey;
  title: string;
}

interface ArchiveCardProps {
  children: React.ReactNode;
  className: string;
  badges: CardBadge[];
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

function clip(text: string | null | undefined, max = 86): string {
  const value = text?.trim();
  if (!value) return "unrecorded";
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1).trim()}…`;
}

function cleanDate(text: string): string {
  return text.replace("T00:00:00Z", "");
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

function table(surface: Surface, kind: SurfaceTable["kind"]): SurfaceTable | undefined {
  return surface.tables.find((item) => item.kind === kind);
}

function rows(surface: Surface, kind: SurfaceTable["kind"], max = 4) {
  return table(surface, kind)?.rows.slice(0, max) ?? [];
}

function folderSamples(folder: Folder, max = 5): Surface[] {
  return sortChronologically(getSurfacesForFolder(folder)).slice(0, max);
}

function evidenceRows(surface: Surface, max = 7) {
  return surface.tables.flatMap((item) =>
    item.rows.map(([key, value]) => ({
      kind: item.kind,
      key,
      value,
    })),
  ).slice(0, max);
}

function CardBadges({ badges }: { badges: CardBadge[] }) {
  return (
    <div className="archive-card__badges" aria-label={badges.map((b) => b.title).join(", ")}>
      {badges.slice(0, 4).map((badge) => (
        <span
          key={`${badge.type}-${badge.title}`}
          className="archive-card__badge"
          title={`${badge.type}: ${badge.title}`}
          style={{ backgroundColor: getFolderInk(badge.type) }}
        >
          <span className="sr-only">{badge.title}</span>
        </span>
      ))}
    </div>
  );
}

function ArchiveCard({ children, className, badges }: ArchiveCardProps) {
  return (
    <article className={`archive-card ${className}`}>
      <CardBadges badges={badges} />
      {children}
    </article>
  );
}

function ImageBay({ surface, quiet = false }: { surface: Surface; quiet?: boolean }) {
  const canRender = isRenderableImage(surface.image);
  return (
    <figure className={`archive-card__image ${quiet ? "archive-card__image--quiet" : ""}`}>
      {canRender ? (
        <img src={surface.image.url ?? undefined} alt="" />
      ) : (
        <div className="archive-card__empty-image">
          <span>{surface.image.state}</span>
        </div>
      )}
      <figcaption>{canRender ? clip(surface.image.credit ?? surface.sourceName, 42) : surface.image.state}</figcaption>
    </figure>
  );
}

function MetaRows({ rows: rowItems }: { rows: Array<[string, string]> }) {
  return (
    <dl className="archive-card__meta">
      {rowItems.map(([key, value]) => (
        <div key={`${key}-${value}`}>
          <dt>{key}</dt>
          <dd>{clip(value, 58)}</dd>
        </div>
      ))}
    </dl>
  );
}

function FolderLine({ folders }: { folders: SurfaceFolderRef[] }) {
  return (
    <p className="archive-card__folder-line">
      {folders.slice(0, 3).map((folder) => folder.title).join(" / ")}
    </p>
  );
}

function SpecimenSquare({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--a-specimen" badges={badgesFromSurface(surface)}>
      <header>
        <p>{surface.sourceRecordId}</p>
        <h2>{surface.title}</h2>
      </header>
      <div className="archive-card__a-body">
        <ImageBay surface={surface} quiet />
        <p className="archive-card__body">{clip(surface.descriptionSummary, 136)}</p>
      </div>
      <MetaRows
        rows={[
          ["date", cleanDate(surface.dateText)],
          ["place", surface.placeText],
          ["medium", surface.medium],
          ["source", surface.sourceName],
        ]}
      />
    </ArchiveCard>
  );
}

function ExhibitionLandscape({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--a-exhibition" badges={badgesFromSurface(surface)}>
      <aside>
        <span>{cleanDate(surface.dateText)}</span>
        <p>{surface.sourceRecordId}</p>
      </aside>
      <section>
        <p>{surface.sourceRecordId}</p>
        <h2>{surface.title}</h2>
        <p className="archive-card__byline">{clip(surface.creator, 92)}</p>
        <p className="archive-card__body">{clip(surface.descriptionSummary || surface.rights.label, 164)}</p>
        <FolderLine folders={surface.folders} />
      </section>
      <ImageBay surface={surface} quiet />
      <MetaRows
        rows={[
          ["medium", surface.medium],
          ["source", surface.sourceName],
          ["rights", surface.rights.displayPolicy],
        ]}
      />
    </ArchiveCard>
  );
}

function TypographyPortrait({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--a-reading" badges={badgesFromSurface(surface)}>
      <header>
        <p>{surface.sourceRecordId}</p>
        <h2>{clip(surface.title, 78)}</h2>
      </header>
      <p className="archive-card__body">{clip(surface.classificationRationale, 150)}</p>
      <MetaRows
        rows={[
          ["date", cleanDate(surface.dateText)],
          ["creator", surface.creator],
          ["source", surface.sourceName],
          ["accessed", surface.accessDate],
          ["reading", `${surface.readingTextLength ?? 0} chars`],
        ]}
      />
      <ol>
        {rows(surface, "CLASSIFICATION", 2).map(([key, value]) => (
          <li key={key}>
            <span>{key}</span>
            {clip(value, 46)}
          </li>
        ))}
      </ol>
    </ArchiveCard>
  );
}

function FolderIndexLandscape({ folder }: { folder: Folder }) {
  const samples = folderSamples(folder, 5);

  return (
    <ArchiveCard
      className="archive-card--a-folder"
      badges={[{ type: folder.type, title: folder.title }]}
    >
      <header>
        <p>{folder.type} folder</p>
        <h2>{folder.title}</h2>
        <span>{spanLabel(folder.dateStart, folder.dateEnd)}</span>
      </header>
      <strong>{folder.surfaceIds.length}</strong>
      <p className="archive-card__body">{clip(folder.scopeNote, 150)}</p>
      <ol>
        {samples.map((surface) => (
          <li key={surface.surfaceId}>
            <span>{cleanDate(surface.dateText)}</span>
            {clip(surface.title, 56)}
          </li>
        ))}
      </ol>
    </ArchiveCard>
  );
}

function ColorRecordCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--color-record" badges={badgesFromSurface(surface)}>
      <header>
        <p>{surface.sourceRecordId}</p>
        <h2>{surface.title}</h2>
      </header>
      <MetaRows
        rows={[
          ["date", cleanDate(surface.dateText)],
          ["place", surface.placeText],
          ["source", surface.sourceName],
          ["image", surface.image.state],
        ]}
      />
    </ArchiveCard>
  );
}

function ColorImageCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--color-image" badges={badgesFromSurface(surface)}>
      <section>
        <p>{surface.sourceRecordId}</p>
        <h2>{surface.title}</h2>
        <p className="archive-card__body">{clip(surface.descriptionSummary || surface.rights.label, 126)}</p>
      </section>
      <ImageBay surface={surface} quiet />
      <FolderLine folders={surface.folders} />
    </ArchiveCard>
  );
}

function ColorTypeCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--color-type" badges={badgesFromSurface(surface)}>
      <p>{surface.sourceRecordId}</p>
      <h2>{clip(surface.title, 82)}</h2>
      <div className="archive-card__color-rule" aria-hidden />
      <MetaRows
        rows={[
          ["creator", surface.creator],
          ["medium", surface.medium],
          ["source", surface.sourceName],
        ]}
      />
    </ArchiveCard>
  );
}

function ColorFolderCard({ folder }: { folder: Folder }) {
  const samples = folderSamples(folder, 4);

  return (
    <ArchiveCard
      className="archive-card--color-folder"
      badges={[{ type: folder.type, title: folder.title }]}
    >
      <header>
        <p>{folder.type} folder</p>
        <h2>{folder.title}</h2>
      </header>
      <strong>{folder.surfaceIds.length}</strong>
      <ol>
        {samples.map((surface) => (
          <li key={surface.surfaceId}>
            <span>{cleanDate(surface.dateText)}</span>
            {clip(surface.title, 50)}
          </li>
        ))}
      </ol>
    </ArchiveCard>
  );
}

function BarcodeMark() {
  return (
    <div className="archive-card__barcode" aria-hidden>
      {Array.from({ length: 18 }, (_, index) => (
        <span key={index} />
      ))}
    </div>
  );
}

function RightsGraphic({ surface }: { surface: Surface }) {
  const policy = surface.rights.displayPolicy.replaceAll("_", " ");
  const basis = clip(surface.rights.label.replace(`${surface.image.state}:`, ""), 42);

  return (
    <div className="archive-card__rights-graphic" aria-label={surface.rights.label}>
      <div className="archive-card__rights-panel">
        <span>authorization check</span>
        <strong>{surface.image.state}</strong>
        <small>graphic surrogate required</small>
      </div>
      <div className="archive-card__rights-checklist" aria-hidden>
        {[
          ["source", surface.sourceRecordId],
          ["image", "withheld"],
          ["reuse", policy],
          ["display", "metadata only"],
        ].map(([key, value]) => (
          <div key={key}>
            <span>{key}</span>
            <i />
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <dl>
        <div>
          <dt>policy</dt>
          <dd>{policy}</dd>
        </div>
        <div>
          <dt>basis</dt>
          <dd>{basis}</dd>
        </div>
      </dl>
    </div>
  );
}

function SpecialStampCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--special-stamp" badges={badgesFromSurface(surface)}>
      <header>
        <p>{surface.sourceRecordId}</p>
        <h2>{clip(surface.title, 58)}</h2>
      </header>
      <ImageBay surface={surface} quiet />
      <p className="archive-card__body">{clip(surface.descriptionSummary, 128)}</p>
      <MetaRows
        rows={[
          ["date", cleanDate(surface.dateText)],
          ["source", surface.sourceName],
          ["medium", surface.medium],
          ["rights", surface.rights.displayPolicy],
        ]}
      />
    </ArchiveCard>
  );
}

function SpecialAdmitCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--special-admit" badges={badgesFromSurface(surface)}>
      <section>
        <p>{surface.sourceRecordId}</p>
        <h2>{clip(surface.title, 64)}</h2>
        <p className="archive-card__body">{clip(surface.descriptionSummary || surface.rights.label, 118)}</p>
      </section>
      <strong>{cleanDate(surface.dateText)}</strong>
      <div className="archive-card__ticket-stub">
        <span>ADMIT</span>
        <p>{surface.image.state}</p>
      </div>
      <MetaRows
        rows={[
          ["creator", surface.creator],
          ["source", surface.sourceName],
          ["rights", surface.rights.displayPolicy],
        ]}
      />
    </ArchiveCard>
  );
}

function SpecialPunchCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--special-punch" badges={badgesFromSurface(surface)}>
      <RightsGraphic surface={surface} />
      <div className="archive-card__ticket-date">
        <span>{surface.dateStart ?? "date"}</span>
        <span>{surface.image.state}</span>
      </div>
      <h2>{clip(surface.title, 42)}</h2>
      <FolderLine folders={surface.folders} />
      <BarcodeMark />
      <MetaRows
        rows={[
          ["source", surface.sourceName],
          ["medium", surface.medium],
        ]}
      />
    </ArchiveCard>
  );
}

function SpecialChamferCard({ folder, surface }: { folder: Folder; surface: Surface }) {
  const samples = folderSamples(folder, 4);

  return (
    <ArchiveCard
      className="archive-card--special-chamfer"
      badges={[{ type: folder.type, title: folder.title }, ...badgesFromSurface(surface).slice(0, 2)]}
    >
      <section className="archive-card__chamfer-left">
        <p>{folder.type} folder</p>
        <h2>{folder.title}</h2>
        <div>
          <strong>{folder.surfaceIds.length}</strong>
          <span>{spanLabel(folder.dateStart, folder.dateEnd)}</span>
        </div>
      </section>
      <section className="archive-card__chamfer-right">
        <p>{surface.sourceRecordId}</p>
        <h3>{clip(surface.title, 72)}</h3>
        <MetaRows
          rows={[
            ["date", cleanDate(surface.dateText)],
            ["source", surface.sourceName],
            ["status", surface.rights.displayPolicy],
          ]}
        />
      </section>
      <ol>
        {samples.map((item) => (
          <li key={item.surfaceId}>
            <span>{cleanDate(item.dateText)}</span>
            {clip(item.title, 52)}
          </li>
        ))}
      </ol>
    </ArchiveCard>
  );
}

function DenseWorkOrderCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--dense-work-order" badges={badgesFromSurface(surface)}>
      <header>
        <div>
          <span>record receipt</span>
          <strong>{surface.sourceRecordId}</strong>
        </div>
        <div>
          <span>date</span>
          <strong>{cleanDate(surface.dateText)}</strong>
        </div>
        <div>
          <span>pieces</span>
          <strong>{surface.tables.length}</strong>
        </div>
      </header>
      <section className="archive-card__dense-address">
        <p>name</p>
        <strong>{clip(surface.title, 52)}</strong>
        <p>source</p>
        <strong>{clip(surface.sourceName, 44)}</strong>
      </section>
      <div className="archive-card__dense-week">
        {["region", "theme", "medium", "rights", "source", "cite", "note"].map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
      <section className="archive-card__dense-description">
        <p>description</p>
        <strong>{clip(surface.descriptionSummary || surface.classificationRationale, 180)}</strong>
      </section>
      <MetaRows
        rows={[
          ["creator", surface.creator],
          ["medium", surface.medium],
          ["rights", surface.rights.displayPolicy],
          ["accessed", surface.accessDate],
        ]}
      />
    </ArchiveCard>
  );
}

function DenseTicketPairCard({ surfaces }: { surfaces: [Surface, Surface] }) {
  return (
    <div className="archive-card__dense-ticket-stack" aria-label="paired compact source tickets">
      {surfaces.map((surface, index) => (
        <ArchiveCard
          key={surface.surfaceId}
          className="archive-card--dense-ticket"
          badges={badgesFromSurface(surface)}
        >
          <header>
            <span>FIG.{String(index + 5).padStart(3, "0")}</span>
            <strong>{clip(surface.title, 42)}</strong>
            <span>{cleanDate(surface.dateText)}</span>
          </header>
          <div className="archive-card__dense-burst" aria-hidden>
            <i />
            <b>{surface.image.state}</b>
          </div>
          <section>
            <p>{clip(surface.sourceName, 34)}</p>
            <p>{clip(surface.creator, 36)}</p>
            <p>{clip(surface.medium, 42)}</p>
          </section>
        </ArchiveCard>
      ))}
    </div>
  );
}

function DenseTravelLabelCard({ folder, surface }: { folder: Folder; surface: Surface }) {
  const samples = folderSamples(folder, 4);

  return (
    <ArchiveCard
      className="archive-card--dense-travel-label"
      badges={[{ type: folder.type, title: folder.title }, ...badgesFromSurface(surface).slice(0, 3)]}
    >
      <header>
        <span>archive transit / source slip</span>
        <h2>{folder.title}</h2>
        <strong>{spanLabel(folder.dateStart, folder.dateEnd)}</strong>
      </header>
      <div className="archive-card__dense-label-grid">
        <span>origin</span>
        <strong>{clip(surface.sourceName, 32)}</strong>
        <span>record</span>
        <strong>{surface.sourceRecordId}</strong>
        <span>routing</span>
        <strong>{surface.image.state} / {surface.rights.displayPolicy}</strong>
      </div>
      <ol>
        {samples.map((item) => (
          <li key={item.surfaceId}>
            <span>{cleanDate(item.dateText)}</span>
            <strong>{clip(item.title, 48)}</strong>
          </li>
        ))}
      </ol>
      <BarcodeMark />
    </ArchiveCard>
  );
}

function DenseIdentityCard({ surface }: { surface: Surface }) {
  const sourceRows = rows(surface, "SOURCE", 4);

  return (
    <ArchiveCard className="archive-card--dense-identity" badges={badgesFromSurface(surface)}>
      <header>
        <h2>{clip(surface.title, 44)}</h2>
        <p>{clip(surface.medium, 52)}</p>
      </header>
      <section>
        <p>{clip(surface.descriptionSummary, 160)}</p>
      </section>
      <MetaRows
        rows={[
          ["date", cleanDate(surface.dateText)],
          ["creator", surface.creator],
          ["source", surface.sourceName],
        ]}
      />
      <ol>
        {sourceRows.map(([key, value]) => (
          <li key={key}>
            <span>{key}</span>
            {clip(value, 38)}
          </li>
        ))}
      </ol>
    </ArchiveCard>
  );
}

function DenseQuoteBadgeCard({ surface }: { surface: Surface }) {
  const quote = surface.descriptionSummary || surface.classificationRationale || surface.title;

  return (
    <ArchiveCard className="archive-card--dense-quote-badge" badges={badgesFromSurface(surface)}>
      <p>{surface.sourceRecordId}</p>
      <h2>{clip(quote, 118)}</h2>
      <section>
        <strong>{cleanDate(surface.dateText)}</strong>
        <span>{clip(surface.title, 62)}</span>
      </section>
      <div className="archive-card__quote-fields">
        {evidenceRows(surface, 6).map((row) => (
          <div key={`${row.kind}-${row.key}`}>
            <span>{row.kind}</span>
            <strong>{row.key}</strong>
            <p>{clip(row.value, 70)}</p>
          </div>
        ))}
      </div>
    </ArchiveCard>
  );
}

function RightsReviewCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--rights-review" badges={badgesFromSurface(surface)}>
      <header>
        <p>{surface.sourceRecordId}</p>
        <h2>{surface.title}</h2>
      </header>
      <ImageBay surface={surface} quiet />
      <p className="archive-card__body">{clip(surface.rights.label, 152)}</p>
      <MetaRows rows={rows(surface, "RIGHTS", 4)} />
    </ArchiveCard>
  );
}

function SourceWideCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--source-wide" badges={badgesFromSurface(surface)}>
      <section>
        <p>{surface.sourceRecordId}</p>
        <h2>{surface.title}</h2>
        <p className="archive-card__byline">{clip(surface.creator, 76)}</p>
        <p className="archive-card__body">{clip(surface.descriptionSummary || surface.rights.label, 142)}</p>
      </section>
      <ImageBay surface={surface} quiet />
      <MetaRows
        rows={[
          ["date", cleanDate(surface.dateText)],
          ["source", surface.sourceName],
          ["identifier", surface.sourceRecordId],
          ["medium", surface.medium],
          ["rights", surface.rights.displayPolicy],
          ["accessed", surface.accessDate],
        ]}
      />
    </ArchiveCard>
  );
}

function PublicationCard({ surface }: { surface: Surface }) {
  return (
    <ArchiveCard className="archive-card--publication" badges={badgesFromSurface(surface)}>
      <header>
        <p>{surface.sourceRecordId}</p>
        <h2>{surface.title}</h2>
        <span>{cleanDate(surface.dateText)}</span>
      </header>
      <div className="archive-card__rule-graphic" aria-hidden>
        <span />
        <span />
        <span />
      </div>
      <p className="archive-card__body">{clip(surface.descriptionSummary, 156)}</p>
      <MetaRows
        rows={[
          ["creator", surface.creator],
          ["medium", surface.medium],
          ["source", surface.sourceName],
          ["status", surface.rights.displayPolicy],
        ]}
      />
    </ArchiveCard>
  );
}

function FolderTimelineCard({ folder }: { folder: Folder }) {
  const samples = folderSamples(folder, 6);

  return (
    <ArchiveCard
      className="archive-card--folder-timeline"
      badges={[{ type: folder.type, title: folder.title }]}
    >
      <header>
        <p>{folder.type} folder</p>
        <h2>{folder.title}</h2>
      </header>
      <div className="archive-card__folder-stat">
        <span>{spanLabel(folder.dateStart, folder.dateEnd)}</span>
        <strong>{folder.surfaceIds.length}</strong>
      </div>
      <ol>
        {samples.map((surface) => (
          <li key={surface.surfaceId}>
            <span>{cleanDate(surface.dateText)}</span>
            <p>{clip(surface.title, 68)}</p>
          </li>
        ))}
      </ol>
    </ArchiveCard>
  );
}

export function ArchiveCardSurface({
  surface,
  layoutId,
}: {
  surface: Surface;
  layoutId?: ArchiveCardLayoutId;
}) {
  const resolved = layoutId ?? selectArchiveCardLayout(surface);
  if (resolved === "CARD01.specimen-square") return <SpecimenSquare surface={surface} />;
  if (resolved === "CARD02.typography-portrait") return <TypographyPortrait surface={surface} />;
  if (resolved === "CARD04.source-wide") return <SourceWideCard surface={surface} />;
  if (resolved === "CARD05.publication") return <PublicationCard surface={surface} />;
  return <RightsReviewCard surface={surface} />;
}

export default function CardLab({ mode = "all" }: { mode?: CardMode }) {
  const specimen = mustSurface("SURF-GAX1970R006");
  const ascot = mustSurface("SURF-ER1830R073");
  const kiss = mustSurface("SURF-MC1930R056");
  const dwan = mustSurface("SURF-MC1930R077");
  const graphicDesign = mustSurface("SURF-MX1970R027");
  const costume = mustSurface("SURF-MC1930R007");
  const danza = mustSurface("SURF-MC1930R071");
  const jewishMuseum = mustSurface("SURF-MC1930R072");
  const johnWilliams = mustSurface("SURF-SI1970R001");
  const trident = mustSurface("SURF-GAPIT2026R025");
  const france = mustFolder("region", "france");
  const travel = mustFolder("theme", "travel-and-transport-poster-culture");
  const typography = mustFolder("theme", "modern-typography-and-layout");
  const showA = mode === "all" || mode === "square";
  const showB = mode === "all" || mode === "rectangle";
  const showC = mode === "all" || mode === "color";
  const showSpecial = mode === "all" || mode === "special";
  const showDense = mode === "all" || mode === "dense";

  return (
    <main className="card-lab card-lab--archive" data-mode={mode}>
      {showA ? (
        <section className="card-lab__set card-lab__set--archive" aria-label="Card layout family A">
          <SpecimenSquare surface={specimen} />
          <ExhibitionLandscape surface={kiss} />
          <TypographyPortrait surface={specimen} />
          <FolderIndexLandscape folder={france} />
        </section>
      ) : null}
      {showB ? (
        <section className="card-lab__set card-lab__set--archive" aria-label="Card layout family B">
          <RightsReviewCard surface={ascot} />
          <SourceWideCard surface={dwan} />
          <PublicationCard surface={graphicDesign} />
          <FolderTimelineCard folder={travel} />
        </section>
      ) : null}
      {showC ? (
        <section className="card-lab__set card-lab__set--archive card-lab__set--color" aria-label="Card layout family C">
          <ColorRecordCard surface={specimen} />
          <ColorImageCard surface={kiss} />
          <ColorTypeCard surface={graphicDesign} />
          <ColorFolderCard folder={typography} />
        </section>
      ) : null}
      {showSpecial ? (
        <section className="card-lab__set card-lab__set--archive card-lab__set--special" aria-label="Special proportion card layouts">
          <SpecialStampCard surface={specimen} />
          <SpecialAdmitCard surface={kiss} />
          <SpecialPunchCard surface={ascot} />
          <SpecialChamferCard folder={travel} surface={graphicDesign} />
        </section>
      ) : null}
      {showDense ? (
        <section
          className="card-lab__set card-lab__set--archive card-lab__set--dense"
          aria-label="High capacity card layouts"
          data-card-group="dense"
        >
          <DenseWorkOrderCard surface={costume} />
          <DenseTicketPairCard surfaces={[danza, jewishMuseum]} />
          <DenseTravelLabelCard folder={travel} surface={ascot} />
          <DenseIdentityCard surface={johnWilliams} />
          <DenseQuoteBadgeCard surface={trident} />
        </section>
      ) : null}
    </main>
  );
}
