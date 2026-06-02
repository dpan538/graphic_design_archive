import type { FolderTypeKey, Surface, SurfaceTable, TableRow } from "@/types/archive";
import { getFolderInk, getSurface } from "@/lib/archive-data";
import {
  type SourceSlipLayoutId,
  selectSourceSlipLayout,
} from "@/lib/slip-layout";
import type { ArchiveCardLayoutId } from "@/lib/card-asset-layout";

interface SlipProps {
  surface: Surface;
}

function mustSurface(id: string): Surface {
  const surface = getSurface(id);
  if (!surface) throw new Error(`Missing slip test surface: ${id}`);
  return surface;
}

function clip(text: string | null | undefined, max = 72): string {
  const value = text?.replace(/\s+/g, " ").trim();
  if (!value) return "unrecorded";
  if (value.length <= max) return value;
  return `${value.slice(0, max - 3).trim()}...`;
}

function cleanDate(text: string): string {
  return text.replace("T00:00:00Z", "");
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

function shortUrl(url: string): string {
  return url.replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/\/$/, "");
}

function folderDots(surface: Surface) {
  return surface.folders.slice(0, 4).map((folder) => ({
    type: folder.type as FolderTypeKey,
    title: folder.title,
  }));
}

function SlipDots({ surface }: SlipProps) {
  return (
    <div className="source-slip__dots" aria-label={surface.folders.map((f) => f.title).join(", ")}>
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

function ReceiptRows({ items, max = 8 }: { items: TableRow[]; max?: number }) {
  return (
    <dl className="source-slip__rows">
      {items.slice(0, max).map(([key, value]) => (
        <div key={`${key}-${value}`}>
          <dt>{key}</dt>
          <dd>{clip(value, 78)}</dd>
        </div>
      ))}
    </dl>
  );
}

function SourceSquareSlip({ surface }: SlipProps) {
  const source = rows(surface, "SOURCE", 6);
  const normalized = rows(surface, "NORMALIZED", 4);

  return (
    <article className="source-slip source-slip--square" aria-label="Square source slip">
      <SlipDots surface={surface} />
      <header>
        <p>MGD Archive</p>
        <h2>Source Receipt</h2>
        <span>{surface.surfaceId}</span>
      </header>
      <section className="source-slip__receipt-head">
        <p>{surface.sourceName}</p>
        <strong>{surface.sourceRecordId}</strong>
        <span>{cleanDate(surface.dateText)}</span>
      </section>
      <section className="source-slip__title-block">
        <p>{clip(surface.title, 92)}</p>
        <span>{clip(surface.creator, 62)}</span>
      </section>
      <ReceiptRows items={[...source, ...normalized]} max={8} />
      <footer>
        <span>{surface.image.state}</span>
        <span>{shortUrl(rowValue(surface, "CITATIONS", /source url/i))}</span>
      </footer>
    </article>
  );
}

function CitationPortraitSlip({ surface }: SlipProps) {
  const citation = rows(surface, "CITATIONS", 4);
  const rights = rows(surface, "RIGHTS", 5);
  const classification = rows(surface, "CLASSIFICATION", 5);

  return (
    <article className="source-slip source-slip--portrait" aria-label="Three by four citation slip">
      <SlipDots surface={surface} />
      <header>
        <p>MGD Archive / citation slip</p>
        <h2>{clip(surface.title, 74)}</h2>
        <span>{surface.provisionalDisplayNumber}</span>
      </header>
      <section className="source-slip__ticket-line">
        <span>source</span>
        <strong>{surface.sourceRecordId}</strong>
        <span>{cleanDate(surface.accessDate)}</span>
      </section>
      <ReceiptRows items={citation} max={4} />
      <section className="source-slip__split">
        <div>
          <h3>rights</h3>
          <ReceiptRows items={rights} max={5} />
        </div>
        <div>
          <h3>filing</h3>
          <ReceiptRows items={classification} max={4} />
        </div>
      </section>
      <p className="source-slip__note">{clip(surface.citationBasis || surface.rights.label, 176)}</p>
      <footer>
        <span>{surface.sourceName}</span>
        <span>{surface.image.state}</span>
      </footer>
    </article>
  );
}

function NarrowReturnSlip({ surface }: SlipProps) {
  const source = rows(surface, "SOURCE", 6);
  const normalized = rows(surface, "NORMALIZED", 5);
  const relations = rows(surface, "RELATIONS", 4);

  return (
    <article className="source-slip source-slip--narrow" aria-label="Narrow source return slip">
      <SlipDots surface={surface} />
      <header>
        <p>MGD Archive</p>
        <h2>Source Return</h2>
        <span>{surface.seqLabel}</span>
      </header>
      <section className="source-slip__stamp">
        <strong>{surface.image.state}</strong>
        <span>{surface.rights.displayPolicy}</span>
      </section>
      <section className="source-slip__narrow-title">
        <p>{clip(surface.title, 86)}</p>
        <span>{surface.sourceRecordId}</span>
      </section>
      <ReceiptRows items={source} max={5} />
      <div className="source-slip__rule" aria-hidden />
      <ReceiptRows items={[...normalized, ...relations]} max={6} />
      <footer>
        <span>{cleanDate(surface.dateText)}</span>
        <span>{clip(surface.folders[0]?.title, 34)}</span>
      </footer>
    </article>
  );
}

export function ArchiveSlipSurface({
  surface,
  layoutId,
  cardLayoutId,
}: {
  surface: Surface;
  layoutId?: SourceSlipLayoutId;
  cardLayoutId?: ArchiveCardLayoutId;
}) {
  const resolved =
    layoutId ??
    selectSourceSlipLayout(surface, cardLayoutId ?? "CARD02.typography-portrait");
  if (resolved === "SLIP01.square") return <SourceSquareSlip surface={surface} />;
  if (resolved === "SLIP02.portrait") return <CitationPortraitSlip surface={surface} />;
  return <NarrowReturnSlip surface={surface} />;
}

export default function SlipLab() {
  const dwan = mustSurface("SURF-MC1930R077");
  const gallica = mustSurface("SURF-GAX1970R006");
  const ascot = mustSurface("SURF-ER1830R073");

  return (
    <main className="source-slip-lab">
      <header className="source-slip-lab__header">
        <p>Source Slip / Citation Slip</p>
        <h1>MGD Archive receipt set</h1>
        <dl>
          <div>
            <dt>count</dt>
            <dd>3</dd>
          </div>
          <div>
            <dt>orientation</dt>
            <dd>vertical</dd>
          </div>
          <div>
            <dt>density</dt>
            <dd>high text</dd>
          </div>
        </dl>
      </header>
      <section className="source-slip-lab__grid" aria-label="Source and citation slip studies">
        <SourceSquareSlip surface={dwan} />
        <CitationPortraitSlip surface={gallica} />
        <NarrowReturnSlip surface={ascot} />
      </section>
    </main>
  );
}
