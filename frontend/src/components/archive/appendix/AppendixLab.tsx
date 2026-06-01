import type { FolderTypeKey, Surface, SurfaceTable, TableRow } from "@/types/archive";
import { getFolderInk, getSurface } from "@/lib/archive-data";
import type { AppendixLayoutId } from "@/lib/appendix-layout";

type AppendixTone = "rights" | "citation" | "relations" | "context" | "statement" | "index";

interface AppendixShellProps {
  children: React.ReactNode;
  surface: Surface;
  className: string;
  label: string;
  tone: AppendixTone;
}

function mustSurface(id: string): Surface {
  const surface = getSurface(id);
  if (!surface) throw new Error(`Missing appendix test surface: ${id}`);
  return surface;
}

function clip(text: string | null | undefined, max = 110): string {
  const value = text?.replace(/\s+/g, " ").trim();
  if (!value) return "unrecorded";
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1).trim()}...`;
}

function table(surface: Surface, kind: SurfaceTable["kind"]): SurfaceTable | undefined {
  return surface.tables.find((item) => item.kind === kind);
}

function rows(surface: Surface, kind: SurfaceTable["kind"], max = 8): TableRow[] {
  return table(surface, kind)?.rows.slice(0, max) ?? [];
}

function rowValue(surface: Surface, kind: SurfaceTable["kind"], label: RegExp): string {
  return table(surface, kind)?.rows.find(([key]) => label.test(key))?.[1] ?? "unrecorded";
}

function cleanDate(text: string): string {
  return text.replace("T00:00:00Z", "");
}

function shortUrl(url: string): string {
  return url.replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/\/$/, "");
}

function citationLinks(surface: Surface): string[] {
  const sourceLinks = rowValue(surface, "CITATIONS", /source url|source links/i);
  return sourceLinks
    .split(";")
    .map((item) => item.trim())
    .filter(Boolean);
}

function folderDots(surface: Surface) {
  return surface.folders.slice(0, 4).map((folder) => ({
    type: folder.type as FolderTypeKey,
    title: folder.title,
  }));
}

function FolderDots({ surface }: { surface: Surface }) {
  return (
    <div className="appendix-dots" aria-label={surface.folders.map((f) => f.title).join(", ")}>
      {folderDots(surface).map((folder) => (
        <span
          key={`${folder.type}-${folder.title}`}
          title={`${folder.type}: ${folder.title}`}
          style={{ backgroundColor: getFolderInk(folder.type) }}
        />
      ))}
    </div>
  );
}

function AppendixShell({ children, surface, className, label, tone }: AppendixShellProps) {
  return (
    <article className={`appendix-sheet ${className}`} data-tone={tone}>
      <FolderDots surface={surface} />
      <span className="appendix-sheet__label">{label}</span>
      {children}
    </article>
  );
}

function MiniRows({ items, max = 6 }: { items: TableRow[]; max?: number }) {
  return (
    <dl className="appendix-mini-rows">
      {items.slice(0, max).map(([key, value]) => (
        <div key={`${key}-${value}`}>
          <dt>{key}</dt>
          <dd>{clip(value, 72)}</dd>
        </div>
      ))}
    </dl>
  );
}

export function RightsEvidenceAppendix({ surface }: { surface: Surface }) {
  const sourceUrl = rowValue(surface, "CITATIONS", /source url/i);
  const accessDate = rowValue(surface, "CITATIONS", /access date/i);
  const rawPayload = rowValue(surface, "CITATIONS", /raw payload/i);
  const sourceIdentifier = rowValue(surface, "SOURCE", /identifier/i);
  const imageState = surface.image.state;
  const isBlankEvidence = imageState === "IMG00";
  const evidencePhrase = isBlankEvidence
    ? "image field intentionally blank"
    : "image display evidence recorded";
  const reviewerCopy = isBlankEvidence
    ? "This appendix keeps the record publishable as metadata while the image remains withheld. The blank area above is deliberate evidence of the display decision."
    : "This appendix records image-use evidence for a displayed or source-hosted image. No image is reproduced on the appendix page; the policy, source return, and rights basis remain the evidence.";

  return (
    <AppendixShell
      surface={surface}
      className="appendix-sheet--rights"
      label="AX01 / rights evidence"
      tone="rights"
    >
      <header className="appendix-rights-letter">
        <p>{accessDate}</p>
        <p>
          <span>to:</span>
          {surface.sourceName}
        </p>
        <p>
          <span>record:</span>
          {surface.surfaceId} / {surface.provisionalDisplayNumber}
        </p>
      </header>
      <header className="appendix-head">
        <p>{surface.sourceRecordId}</p>
        <h2>{clip(surface.title, 92)}</h2>
        <span>{clip(sourceUrl, 86)}</span>
      </header>
      <section className="appendix-rights-blank" aria-label={surface.rights.label}>
        <span>{imageState}</span>
        <p>{evidencePhrase}</p>
      </section>
      <section className="appendix-rights-copy">
        <p>
          <strong>dear source reviewer</strong>
          {clip(surface.rights.label, 176)}
        </p>
        <p>{reviewerCopy}</p>
      </section>
      <div className="appendix-rights-brand" aria-hidden>
        {imageState}
      </div>
      <footer className="appendix-rights-footer">
        <span>{surface.sourceRecordId}</span>
        <span>{sourceIdentifier}</span>
        <span>{shortUrl(sourceUrl)}</span>
      </footer>
      <MiniRows
        items={[
          ["image state", imageState],
          ["display number", surface.provisionalDisplayNumber],
          ["source identifier", sourceIdentifier],
          ["source URL", sourceUrl],
          ["access date", accessDate],
          ["display policy", surface.rights.displayPolicy],
          ["rights basis", surface.rights.label],
          ["local copy permitted", rowValue(surface, "RIGHTS", /local copy/i)],
          ["rights review required", rowValue(surface, "RIGHTS", /review required/i)],
          ["raw payload", rawPayload],
        ]}
        max={8}
      />
    </AppendixShell>
  );
}

export function SourceCitationAppendix({ surface }: { surface: Surface }) {
  const links = citationLinks(surface);
  const sourceRows = rows(surface, "SOURCE", 5);

  return (
    <AppendixShell
      surface={surface}
      className="appendix-sheet--citation"
      label="AX02 / source citation register"
      tone="citation"
    >
      <aside>
        <span>{surface.surfaceId}</span>
        <strong>{String(links.length || sourceRows.length).padStart(2, "0")}</strong>
        <p>source links</p>
      </aside>
      <header>
        <p>{surface.sourceName}</p>
        <h2>{clip(surface.title, 92)}</h2>
      </header>
      <ol className="appendix-citation-list">
        {(links.length ? links : sourceRows.map(([, value]) => value)).slice(0, 8).map((link, index) => (
          <li key={`${link}-${index}`}>
            <span>{String(index + 1).padStart(3, "0")}</span>
            <p>{clip(shortUrl(link), 66)}</p>
          </li>
        ))}
      </ol>
      <div className="appendix-citation-foot">
        <MiniRows items={sourceRows} max={4} />
        <p>{clip(surface.rights.label, 140)}</p>
      </div>
    </AppendixShell>
  );
}

export function RelationsAppendix({ surface }: { surface: Surface }) {
  const classification = rows(surface, "CLASSIFICATION", 6);
  const relations = rows(surface, "RELATIONS", 5);

  return (
    <AppendixShell
      surface={surface}
      className="appendix-sheet--relations"
      label="AX03 / relations classification"
      tone="relations"
    >
      <header className="appendix-head">
        <p>{surface.sourceRecordId}</p>
        <h2>{clip(surface.title, 118)}</h2>
        <span>{surface.sourceName}</span>
      </header>
      <section className="appendix-relation-grid">
        <div>
          <h3>classification</h3>
          <MiniRows items={classification} max={6} />
        </div>
        <div>
          <h3>relations</h3>
          <MiniRows items={relations} max={5} />
        </div>
      </section>
      <ol className="appendix-folder-index">
        {surface.folders.map((folder, index) => (
          <li key={folder.folderId}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <p>{folder.type}</p>
            <strong>{folder.title}</strong>
          </li>
        ))}
      </ol>
      <p className="appendix-caution">
        Relation rows are filing evidence only. Associated-with and folder
        membership do not assert influence or authorship.
      </p>
    </AppendixShell>
  );
}

export function ProtocolContextAppendix({ surface }: { surface: Surface }) {
  const sourceSignal = rowValue(surface, "RIGHTS", /image state/i);
  const rightsBasis = rowValue(surface, "RIGHTS", /rights basis/i);
  const localCopy = rowValue(surface, "RIGHTS", /local copy/i);
  const reviewRequired = rowValue(surface, "RIGHTS", /review required/i);
  const source = rows(surface, "SOURCE", 5);
  const sourceUrl = rowValue(surface, "CITATIONS", /source url/i);
  const reviewRows: TableRow[] = [
    ["project image state", surface.image.state],
    ["source signal", sourceSignal],
    ["display policy", surface.rights.displayPolicy],
    ["review note", surface.rights.label],
    ["rights basis", rightsBasis],
    ["local copy permitted", localCopy],
    ["rights review required", reviewRequired],
  ];

  return (
    <AppendixShell
      surface={surface}
      className="appendix-sheet--context"
      label="AX04 / protocol context packet"
      tone="context"
    >
      <div className="appendix-tabs" aria-hidden>
        <span>SRC</span>
        <span>IMG</span>
        <span>REV</span>
      </div>
      <header className="appendix-head">
        <p>{surface.surfaceId}</p>
        <h2>{clip(surface.title, 86)}</h2>
        <span>{cleanDate(surface.dateText)} / {surface.sourceName}</span>
      </header>
      <section className="appendix-context-body">
        <p>{clip(surface.descriptionSummary, 310)}</p>
        <p>{clip(surface.historicalContextNote, 180)}</p>
      </section>
      <div className="appendix-context-ledger">
        <MiniRows items={reviewRows} max={7} />
        <MiniRows items={source} max={4} />
      </div>
      <footer>
        <span>{surface.image.state}</span>
        <p>{clip(shortUrl(sourceUrl), 86)}</p>
      </footer>
    </AppendixShell>
  );
}

export function SourceStatementAppendix({ surface }: { surface: Surface }) {
  const source = rows(surface, "SOURCE", 8);
  const normalized = rows(surface, "NORMALIZED", 7);
  const rights = rows(surface, "RIGHTS", 5);
  const citations = rows(surface, "CITATIONS", 5);
  const classification = rows(surface, "CLASSIFICATION", 4);
  const sourceUrl = rowValue(surface, "CITATIONS", /source url/i);

  return (
    <AppendixShell
      surface={surface}
      className="appendix-sheet--statement"
      label="AX05 / source statement"
      tone="statement"
    >
      <header>
        <p>{cleanDate(surface.dateText)}</p>
        <p>
          <span>to:</span>
          Archive Box / source verification
        </p>
      </header>
      <section className="appendix-statement-id">
        <p>{surface.sourceName}</p>
        <strong>{surface.sourceRecordId}</strong>
        <span>{surface.surfaceId}</span>
      </section>
      <section className="appendix-statement-body">
        <h2>{clip(surface.title, 96)}</h2>
        <p>{clip(surface.descriptionSummary || surface.citationBasis, 360)}</p>
      </section>
      <div className="appendix-statement-ledgers">
        <section>
          <h3>source register</h3>
          <MiniRows items={source} max={8} />
        </section>
        <section>
          <h3>normalized record</h3>
          <MiniRows items={normalized} max={7} />
        </section>
        <section>
          <h3>rights / citation</h3>
          <MiniRows items={[...rights, ...citations]} max={8} />
        </section>
        <section>
          <h3>filing classification</h3>
          <MiniRows items={classification} max={4} />
        </section>
      </div>
      <ol className="appendix-statement-index">
        {surface.folders.map((folder, index) => (
          <li key={folder.folderId}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{folder.type}</strong>
            <p>{folder.title}</p>
          </li>
        ))}
      </ol>
      <footer>
        <span>{surface.image.state}</span>
        <span>{shortUrl(sourceUrl)}</span>
      </footer>
    </AppendixShell>
  );
}

export function TypedIndexAppendix({ surface }: { surface: Surface }) {
  const source = rows(surface, "SOURCE", 8);
  const normalized = rows(surface, "NORMALIZED", 8);
  const classification = rows(surface, "CLASSIFICATION", 7);
  const relations = rows(surface, "RELATIONS", 5);
  const rights = rows(surface, "RIGHTS", 4);
  const citations = rows(surface, "CITATIONS", 4);
  const indexRows = [
    ...source.map(([, value]) => value),
    ...normalized.map(([, value]) => value),
    ...classification.map(([, value]) => value),
    ...relations.map(([key, value]) => `${key}: ${value}`),
  ];

  return (
    <AppendixShell
      surface={surface}
      className="appendix-sheet--typed-index"
      label="AX06 / typed index"
      tone="index"
    >
      <header>
        <p>{surface.sourceRecordId}</p>
        <h2>{clip(surface.title, 76)}</h2>
        <span>{surface.sourceName}</span>
      </header>
      <ol className="appendix-typed-list">
        {indexRows.slice(0, 24).map((value, index) => (
          <li key={`${value}-${index}`}>
            <span>{String(index + 1).padStart(2, "0")}.</span>
            <p>{clip(value, 68)}</p>
          </li>
        ))}
      </ol>
      <aside className="appendix-typed-rail">
        <section className="appendix-typed-image-state">
          <span>{surface.image.state}</span>
          <p>{clip(surface.rights.label, 104)}</p>
        </section>
        <section>
          <h3>rights</h3>
          <MiniRows items={rights} max={4} />
        </section>
        <section>
          <h3>citations</h3>
          <MiniRows items={citations} max={4} />
        </section>
      </aside>
      <footer>
        <span>{surface.folders[0]?.title ?? "unfiled"}</span>
        <span>{cleanDate(surface.dateText)}</span>
      </footer>
    </AppendixShell>
  );
}

export function AppendixLayout({
  layoutId,
  surface,
}: {
  layoutId: AppendixLayoutId;
  surface: Surface;
}) {
  switch (layoutId) {
    case "AX01.rights":
      return <RightsEvidenceAppendix surface={surface} />;
    case "AX02.citation":
      return <SourceCitationAppendix surface={surface} />;
    case "AX03.relations":
      return <RelationsAppendix surface={surface} />;
    case "AX04.context":
      return <ProtocolContextAppendix surface={surface} />;
    case "AX05.statement":
      return <SourceStatementAppendix surface={surface} />;
    case "AX06.typed-index":
      return <TypedIndexAppendix surface={surface} />;
  }
}

export default function AppendixLab() {
  const aicRights = mustSurface("SURF-ER1830R065");
  const chineseGroup = mustSurface("SURF-MX1970R055-GROUP");
  const iaRelations = mustSurface("SURF-MX1970R033");
  const wellcomeContext = mustSurface("SURF-IR1970R044");
  const bauhausStatement = mustSurface("SURF-MC1930R089");
  const iaIndex = mustSurface("SURF-MX1970R036");

  return (
    <main className="appendix-lab">
      <header className="appendix-lab__header">
        <p>Appendix asset study / first pass</p>
        <h1>Evidence pages</h1>
        <dl>
          <div>
            <dt>layouts</dt>
            <dd>6</dd>
          </div>
          <div>
            <dt>image rule</dt>
            <dd>IMG00 blank</dd>
          </div>
          <div>
            <dt>source</dt>
            <dd>public payload</dd>
          </div>
        </dl>
      </header>
      <section className="appendix-lab__grid" aria-label="Appendix layout studies">
        <AppendixLayout layoutId="AX01.rights" surface={aicRights} />
        <AppendixLayout layoutId="AX02.citation" surface={chineseGroup} />
        <AppendixLayout layoutId="AX03.relations" surface={iaRelations} />
        <AppendixLayout layoutId="AX04.context" surface={wellcomeContext} />
        <AppendixLayout layoutId="AX05.statement" surface={bauhausStatement} />
        <AppendixLayout layoutId="AX06.typed-index" surface={iaIndex} />
      </section>
    </main>
  );
}
