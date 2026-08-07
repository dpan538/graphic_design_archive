import type { Folder, FolderTypeKey, Surface } from "@/types/archive";
import {
  FOLDER_TYPE_ORDER,
  dateSpanLabel,
  getFolder,
  getFolderById,
  getFolderInk,
  getFolderType,
  getSurfacesForFolder,
  imageDistribution,
  sortChronologically,
  sourceCount,
} from "@/lib/archive-data";
import {
  READING_NOTE_LAYOUTS,
  type ReadingNoteLayoutId,
  selectReadingNoteLayout,
} from "@/lib/reading-note-layout";

interface ReadingNoteLayoutProps {
  folder: Folder;
  layoutId?: ReadingNoteLayoutId;
}

interface ReadingNoteContext {
  folder: Folder;
  folderLabel: string;
  layoutId: ReadingNoteLayoutId;
  surfaces: Surface[];
  samples: Surface[];
  imageCounts: ReturnType<typeof imageDistribution>;
  sourceTotal: number;
  color: string;
}

const RECORD_RULES = {
  RN01: { max: 2, title: 54, source: 54 },
  RN02: { leftMax: 3, rightMax: 4, title: 38, source: 42 },
  RN03: { max: 1, title: 48, source: 42 },
  RN04: { max: 3, title: 48, source: 56 },
} as const;

function mustFolder(type: FolderTypeKey, slug: string): Folder {
  const folder = getFolder(type, slug);
  if (!folder) throw new Error(`Missing reading-note test folder: ${type}/${slug}`);
  return folder;
}

function clip(text: string | null | undefined, max = 96): string {
  const value = text?.replace(/\s+/g, " ").trim();
  if (!value) return "unrecorded";
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1).trim()}...`;
}

function clean(text: string | null | undefined): string {
  return text?.replace(/\s+/g, " ").trim() || "unrecorded";
}

function strictFittedSamples(
  surfaces: Surface[],
  max: number,
  limits: { title: number; source: number },
): Surface[] {
  return surfaces
    .filter(
      (surface) =>
        clean(surface.title).length <= limits.title &&
        clean(surface.sourceName).length <= limits.source &&
        !/\.(jpe?g|png|gif|tif|tiff|webp)$/i.test(clean(surface.title)) &&
        !/^\[/.test(clean(surface.title)),
    )
    .slice(0, max);
}

function noteContext(folder: Folder, layoutId?: ReadingNoteLayoutId): ReadingNoteContext {
  const surfaces = sortChronologically(getSurfacesForFolder(folder));
  const resolved = layoutId ?? selectReadingNoteLayout(folder);
  return {
    folder,
    folderLabel: getFolderType(folder.type)?.label ?? folder.type,
    layoutId: resolved,
    surfaces,
    samples: surfaces.slice(0, 10),
    imageCounts: imageDistribution(surfaces),
    sourceTotal: sourceCount(surfaces),
    color: getFolderInk(folder.type),
  };
}

function folderSpan(folder: Folder): string {
  return dateSpanLabel(folder.dateStart, folder.dateEnd);
}

function compactFolderId(folder: Folder): string {
  const typeHead = folder.type.slice(0, 3).toUpperCase();
  const slugHead = folder.slug.split("-")[0]?.slice(0, 4).toUpperCase() ?? "FOLD";
  return `${typeHead}/${slugHead}`;
}

function compactLayoutId(layoutId: ReadingNoteLayoutId): string {
  return layoutId.slice(0, 4);
}

function NoteBadges({ ctx }: { ctx: ReadingNoteContext }) {
  const types = new Set<FolderTypeKey>([ctx.folder.type]);
  for (const folderId of ctx.folder.relatedFolderIds) {
    const related = getFolderById(folderId);
    if (related) types.add(related.type);
  }
  for (const surface of ctx.samples) {
    for (const ref of surface.folders) types.add(ref.type);
  }
  const orderedTypes = FOLDER_TYPE_ORDER.filter((type) => types.has(type));
  return (
    <div className="reading-note__badges" aria-label={`${ctx.folder.title} folder colors`}>
      {orderedTypes.map((type) => (
        <span key={type} title={type} style={{ backgroundColor: getFolderInk(type) }} />
      ))}
    </div>
  );
}

function MicroFooter({ ctx }: { ctx: ReadingNoteContext }) {
  return (
    <footer className="reading-note__footer">
      <span>{compactLayoutId(ctx.layoutId)}</span>
      <span>{compactFolderId(ctx.folder)}</span>
      <span>READING NOTE</span>
    </footer>
  );
}

function SampleRows({
  surfaces,
  max = 5,
  dateMax = 14,
  titleMax = 58,
  sourceMax = 30,
}: {
  surfaces: Surface[];
  max?: number;
  dateMax?: number;
  titleMax?: number;
  sourceMax?: number;
}) {
  return (
    <ol className="reading-note__rows">
      {surfaces.slice(0, max).map((surface) => (
        <li key={surface.surfaceId}>
          <span>{clip(surface.dateText, dateMax)}</span>
          <strong>{clip(surface.title, titleMax)}</strong>
          <em>{clip(surface.sourceName, sourceMax)}</em>
        </li>
      ))}
    </ol>
  );
}

function OpenRecordRows({ surfaces, max = 4 }: { surfaces: Surface[]; max?: number }) {
  const records = strictFittedSamples(surfaces, max, {
    title: RECORD_RULES.RN01.title,
    source: RECORD_RULES.RN01.source,
  });
  return (
    <ol className="reading-note__open-records">
      {records.map((surface) => (
        <li key={surface.surfaceId}>
          <span>{clean(surface.dateText)}</span>
          <strong>{clean(surface.title)}</strong>
          <em>{clean(surface.sourceName)}</em>
        </li>
      ))}
    </ol>
  );
}

function StripRecordRows({ surfaces, max = 4 }: { surfaces: Surface[]; max?: number }) {
  const records = strictFittedSamples(surfaces, max, {
    title: RECORD_RULES.RN02.title,
    source: RECORD_RULES.RN02.source,
  });
  return (
    <ol className="reading-note__strip-records">
      {records.map((surface) => (
        <li key={surface.surfaceId}>
          <span>{clean(surface.dateText)}</span>
          <b>{surface.surfaceId.replace("SURF-", "")}</b>
          <strong>{clean(surface.title)}</strong>
          <em>{clean(surface.sourceName)}</em>
        </li>
      ))}
    </ol>
  );
}

function LedgerRows({ surfaces, max = 4 }: { surfaces: Surface[]; max?: number }) {
  const records = strictFittedSamples(surfaces, max, {
    title: RECORD_RULES.RN04.title,
    source: RECORD_RULES.RN04.source,
  });
  return (
    <>
      {records.map((surface) => (
        <div key={surface.surfaceId} className="reading-note__ledger-row">
          <b>{clean(surface.dateText)}</b>
          <strong>{clean(surface.title)}</strong>
          <em>{clean(surface.sourceName)}</em>
        </div>
      ))}
    </>
  );
}

function FactGrid({ ctx }: { ctx: ReadingNoteContext }) {
  const facts: Array<[string, string]> = [
    ["span", folderSpan(ctx.folder)],
    ["design records", String(ctx.folder.surfaceIds.length)],
    ["sources", String(ctx.sourceTotal)],
    ["image", `00 ${ctx.imageCounts.IMG00} / 04 ${ctx.imageCounts.IMG04}`],
  ];
  return (
    <dl className="reading-note__facts">
      {facts.map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function RN01Stacked({ ctx }: { ctx: ReadingNoteContext }) {
  return (
    <article className="reading-note reading-note--stack" style={{ ["--note-color" as string]: ctx.color }}>
      <section className="reading-note__card reading-note__card--scope">
        <NoteBadges ctx={ctx} />
        <div className="reading-note__spread-title" aria-hidden>
          <span>R</span><span>E</span><span>A</span><span>D</span><span>I</span><span>N</span><span>G</span>
        </div>
        <p className="reading-note__kicker">{ctx.folderLabel} / filter view</p>
        <h2>{ctx.folder.title}</h2>
        <p className="reading-note__scope">{clip(ctx.folder.scopeNote, 76)}</p>
        <FactGrid ctx={ctx} />
      </section>
      <section className="reading-note__card reading-note__card--protocol">
        <header>
          <span>IMAGE POLICY</span>
          <span>READING ORDER</span>
        </header>
        <div className="reading-note__rule-row">
          <p>IMG00 keeps the image bay empty and returns attention to source evidence.</p>
          <p>IMG04 is a text-only signal. It removes the image bay and routes dense evidence to appendix leaves.</p>
        </div>
        <MicroFooter ctx={ctx} />
      </section>
    </article>
  );
}

function RN02PairStrip({ ctx }: { ctx: ReadingNoteContext }) {
  const leftSamples = ctx.surfaces.slice(0, 18);
  const rightSamples = ctx.surfaces.slice(8, 34);
  return (
    <article className="reading-note reading-note--pair-strip" style={{ ["--note-color" as string]: ctx.color }}>
      <section className="reading-note__strip reading-note__strip--left">
        <NoteBadges ctx={ctx} />
        <p className="reading-note__kicker">THEME FOLDER</p>
        <h2>{ctx.folder.title}</h2>
        <p className="reading-note__strip-note">{clean(ctx.folder.scopeNote)}</p>
        <FactGrid ctx={ctx} />
        <StripRecordRows surfaces={leftSamples} max={RECORD_RULES.RN02.leftMax} />
      </section>
      <section className="reading-note__strip reading-note__strip--right">
        <p className="reading-note__kicker">SOURCE EVIDENCE</p>
        <h2>Chronological sample</h2>
        <div className="reading-note__split-rule">
          <span>date</span>
          <span>record</span>
        </div>
        <StripRecordRows surfaces={rightSamples.length > 0 ? rightSamples : leftSamples} max={RECORD_RULES.RN02.rightMax} />
        <dl className="reading-note__strip-mini">
          <div>
            <dt>image policy</dt>
            <dd>IMG00 empty; IMG04 appendix only</dd>
          </div>
          <div>
            <dt>sort order</dt>
            <dd>chronological by reviewed date span</dd>
          </div>
          <div>
            <dt>source count</dt>
            <dd>{ctx.sourceTotal} sources / {ctx.folder.surfaceIds.length} records</dd>
          </div>
        </dl>
        <MicroFooter ctx={ctx} />
      </section>
    </article>
  );
}

function RN03SparseStrip({ ctx }: { ctx: ReadingNoteContext }) {
  const sample = strictFittedSamples(ctx.surfaces, RECORD_RULES.RN03.max, {
    title: RECORD_RULES.RN03.title,
    source: RECORD_RULES.RN03.source,
  })[0] ?? ctx.samples[0];
  return (
    <article className="reading-note reading-note--sparse-strip" style={{ ["--note-color" as string]: ctx.color }}>
      <NoteBadges ctx={ctx} />
      <header>
        <span>{ctx.folder.type}</span>
        <span>{folderSpan(ctx.folder)}</span>
      </header>
      <div className="reading-note__spaced-word" aria-label="reading note">
        <span>R</span><span>E</span><span>A</span><span>D</span>
      </div>
      <h2>{ctx.folder.title}</h2>
      <p>{clean(sample?.title ?? ctx.folder.scopeNote)}</p>
      <div className="reading-note__spaced-word" aria-label="source">
        <span>S</span><span>O</span><span>U</span><span>R</span><span>C</span><span>E</span>
      </div>
      <dl>
        <div>
          <dt>design records</dt>
          <dd>{ctx.folder.surfaceIds.length}</dd>
        </div>
        <div>
          <dt>image</dt>
          <dd>{sample?.image.state ?? "IMG00"}</dd>
        </div>
        <div>
          <dt>source</dt>
          <dd>{clip(sample?.sourceName, 34)}</dd>
        </div>
      </dl>
      <MicroFooter ctx={ctx} />
    </article>
  );
}

function RN04Ledger({ ctx }: { ctx: ReadingNoteContext }) {
  return (
    <article className="reading-note reading-note--ledger" style={{ ["--note-color" as string]: ctx.color }}>
      <NoteBadges ctx={ctx} />
      <header>
        <p className="reading-note__kicker">{ctx.folderLabel} reading note</p>
        <h2>{ctx.folder.title}</h2>
        <span>{folderSpan(ctx.folder)}</span>
      </header>
      <div className="reading-note__wavy-rule" aria-hidden />
      <p className="reading-note__scope">{clip(ctx.folder.scopeNote, 150)}</p>
      <FactGrid ctx={ctx} />
      <div className="reading-note__ledger-grid">
        <span>DATE</span>
        <span>TITLE</span>
        <span>SOURCE</span>
        <LedgerRows surfaces={ctx.surfaces} max={RECORD_RULES.RN04.max} />
      </div>
      <MicroFooter ctx={ctx} />
    </article>
  );
}

export function ReadingNoteLayout({ folder, layoutId }: ReadingNoteLayoutProps) {
  const ctx = noteContext(folder, layoutId);
  if (ctx.layoutId === "RN01.stack") return <RN01Stacked ctx={ctx} />;
  if (ctx.layoutId === "RN02.pair-strip") return <RN02PairStrip ctx={ctx} />;
  if (ctx.layoutId === "RN03.sparse-strip") return <RN03SparseStrip ctx={ctx} />;
  return <RN04Ledger ctx={ctx} />;
}

export default function ReadingNoteLab() {
  const notes: Array<[ReadingNoteLayoutId, Folder]> = [
    ["RN01.stack", mustFolder("region", "united-kingdom")],
    ["RN02.pair-strip", mustFolder("theme", "travel-and-transport-poster-culture")],
    ["RN03.sparse-strip", mustFolder("region", "belgium")],
    ["RN04.ledger", mustFolder("medium", "publication-design")],
  ];
  return (
    <main className="reading-note-lab">
      <header className="reading-note-lab__header">
        <p>MGD Archive / replacement asset</p>
        <h1>Reading Note</h1>
        <dl>
          {notes.map(([layoutId]) => (
            <div key={layoutId}>
              <dt>{layoutId}</dt>
              <dd>{READING_NOTE_LAYOUTS[layoutId].label}</dd>
            </div>
          ))}
        </dl>
      </header>
      <section className="reading-note-lab__grid" aria-label="Reading note layouts">
        <div className="reading-note-lab__row reading-note-lab__row--all">
          {notes.map(([layoutId, folder]) => (
            <ReadingNoteLayout key={layoutId} folder={folder} layoutId={layoutId} />
          ))}
        </div>
      </section>
    </main>
  );
}
