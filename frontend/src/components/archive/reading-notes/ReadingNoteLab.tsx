import type { Folder, FolderTypeKey, Surface } from "@/types/archive";
import {
  dateSpanLabel,
  getFolder,
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

function noteContext(folder: Folder, layoutId?: ReadingNoteLayoutId): ReadingNoteContext {
  const surfaces = sortChronologically(getSurfacesForFolder(folder));
  const resolved = layoutId ?? selectReadingNoteLayout(folder);
  return {
    folder,
    folderLabel: getFolderType(folder.type)?.label ?? folder.type,
    layoutId: resolved,
    surfaces,
    samples: surfaces.slice(0, 8),
    imageCounts: imageDistribution(surfaces),
    sourceTotal: sourceCount(surfaces),
    color: getFolderInk(folder.type),
  };
}

function folderSpan(folder: Folder): string {
  return dateSpanLabel(folder.dateStart, folder.dateEnd);
}

function compactFolderId(folder: Folder): string {
  const slugHead = folder.slug.split("-").slice(0, 2).join("-");
  return `${folder.type.toUpperCase()}/${slugHead}`;
}

function NoteBadges({ ctx }: { ctx: ReadingNoteContext }) {
  const types = new Set<FolderTypeKey>([ctx.folder.type]);
  for (const surface of ctx.samples) {
    for (const ref of surface.folders) types.add(ref.type);
  }
  return (
    <div className="reading-note__badges" aria-label={`${ctx.folder.title} folder colors`}>
      {[...types].slice(0, 4).map((type) => (
        <span key={type} style={{ backgroundColor: getFolderInk(type) }} />
      ))}
    </div>
  );
}

function MicroFooter({ ctx }: { ctx: ReadingNoteContext }) {
  return (
    <footer className="reading-note__footer">
      <span>{ctx.layoutId}</span>
      <span>{compactFolderId(ctx.folder)}</span>
      <span>READING NOTE</span>
    </footer>
  );
}

function SampleRows({ surfaces, max = 5 }: { surfaces: Surface[]; max?: number }) {
  return (
    <ol className="reading-note__rows">
      {surfaces.slice(0, max).map((surface) => (
        <li key={surface.surfaceId}>
          <span>{clip(surface.dateText, 14)}</span>
          <strong>{clip(surface.title, 58)}</strong>
          <em>{clip(surface.sourceName, 30)}</em>
        </li>
      ))}
    </ol>
  );
}

function FactGrid({ ctx }: { ctx: ReadingNoteContext }) {
  const facts: Array<[string, string]> = [
    ["span", folderSpan(ctx.folder)],
    ["surfaces", String(ctx.folder.surfaceIds.length)],
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
        <p className="reading-note__scope">{clip(ctx.folder.scopeNote, 168)}</p>
        <FactGrid ctx={ctx} />
      </section>
      <section className="reading-note__card reading-note__card--protocol">
        <header>
          <span>IMAGE POLICY</span>
          <span>READING ORDER</span>
        </header>
        <div className="reading-note__rule-row">
          <p>IMG00 keeps the image bay empty and returns attention to source evidence.</p>
          <p>IMG04 removes the image bay and sends table overflow to appendix leaves.</p>
        </div>
        <SampleRows surfaces={ctx.samples} max={4} />
        <MicroFooter ctx={ctx} />
      </section>
    </article>
  );
}

function RN02PairStrip({ ctx }: { ctx: ReadingNoteContext }) {
  const leftSamples = ctx.samples.slice(0, 4);
  const rightSamples = ctx.samples.slice(4, 8);
  return (
    <article className="reading-note reading-note--pair-strip" style={{ ["--note-color" as string]: ctx.color }}>
      <section className="reading-note__strip reading-note__strip--left">
        <NoteBadges ctx={ctx} />
        <p className="reading-note__kicker">SCHEDULE</p>
        <h2>{ctx.folder.title}</h2>
        <FactGrid ctx={ctx} />
        <SampleRows surfaces={leftSamples} max={4} />
      </section>
      <section className="reading-note__strip reading-note__strip--right">
        <p className="reading-note__kicker">EXPLORE</p>
        <div className="reading-note__split-rule">
          <span>source</span>
          <span>note</span>
        </div>
        <SampleRows surfaces={rightSamples.length > 0 ? rightSamples : leftSamples} max={4} />
        <p className="reading-note__scope">{clip(ctx.folder.scopeNote, 120)}</p>
        <MicroFooter ctx={ctx} />
      </section>
    </article>
  );
}

function RN03SparseStrip({ ctx }: { ctx: ReadingNoteContext }) {
  const sample = ctx.samples[0];
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
      <p>{clip(sample?.title ?? ctx.folder.scopeNote, 76)}</p>
      <div className="reading-note__spaced-word" aria-label="source">
        <span>S</span><span>O</span><span>U</span><span>R</span><span>C</span><span>E</span>
      </div>
      <dl>
        <div>
          <dt>surfaces</dt>
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
        {ctx.samples.slice(0, 5).map((surface) => (
          <div key={surface.surfaceId} className="reading-note__ledger-row">
            <b>{surface.dateText}</b>
            <strong>{clip(surface.title, 44)}</strong>
            <em>{clip(surface.sourceName, 24)}</em>
          </div>
        ))}
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
    ["RN03.sparse-strip", mustFolder("region", "india")],
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
        {notes.map(([layoutId, folder]) => (
          <ReadingNoteLayout key={layoutId} folder={folder} layoutId={layoutId} />
        ))}
      </section>
    </main>
  );
}
