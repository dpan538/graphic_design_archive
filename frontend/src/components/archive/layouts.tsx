import type { Surface, SurfaceImage } from "@/types/archive";
import { type Leaf } from "@/lib/paginate";
import { isRenderableImage } from "@/lib/layout";
import { dateSpanLabel, getFolderType } from "@/lib/archive-data";
import ImageZone from "./ImageZone";
import { ImgBadge, StatusChip, TypeSwatch } from "./primitives";
import {
  MembershipsBlock,
  ProvenanceLine,
  RightsBlock,
  ScopeBlock,
  SourceBlock,
  SourceTextBlock,
  SpecTables,
  TitleBlock,
  UncertaintyBlock,
} from "./blocks";

/**
 * Reusable A4 layouts. Each fills the slot contract from the payload and fits
 * inside one non-scrolling leaf. Every leaf shares a consistent header band
 * (context + accession number) so numbering sits in a fixed place and never
 * overlaps the content. The folder-colour bar is drawn by LeafFrame.
 */

export interface LeafCtx {
  onJump?: (leafIndex: number) => void;
  surfaceLeafIndex?: Map<string, number>;
}

interface LayoutProps {
  leaf: Leaf;
  activeFolderId?: string;
  ctx?: LeafCtx;
}

// ---- shared header band + footer ---------------------------------------

function accessionOf(leaf: Leaf): { no: string; pg: string } {
  if (leaf.type === "register") {
    return {
      no: leaf.folder?.folderId ?? "",
      pg: `Index ${leaf.regPageNumber ?? 1} / ${leaf.regPageCount ?? 1}`,
    };
  }
  return {
    no: leaf.surface?.provisionalDisplayNumber ?? "",
    pg: `p${String(leaf.surfacePageNumber ?? 1).padStart(2, "0")} / ${String(
      leaf.surfacePageCount ?? 1,
    ).padStart(2, "0")}`,
  };
}

function LeafHead({
  leaf,
  context,
  swatch,
}: {
  leaf: Leaf;
  context: React.ReactNode;
  swatch?: React.ReactNode;
}) {
  const acc = accessionOf(leaf);
  return (
    <div className="leaf__head">
      <div className="leaf__context">
        {swatch}
        {context}
      </div>
      <div className="leaf__accession">
        <div className="acc-no">{acc.no}</div>
        <div className="acc-pg">{acc.pg}</div>
      </div>
    </div>
  );
}

function SheetMarkers({ leaf }: { leaf: Leaf }) {
  const s = leaf.surface;
  return (
    <div className="sheet-markers">
      <span>{leaf.layoutId}</span>
      <span>{s ? s.seqLabel : leaf.folder?.folderId}</span>
      <span>Archive Box</span>
    </div>
  );
}

function imagesOf(surface: Surface): SurfaceImage[] {
  const list: SurfaceImage[] = [];
  if (surface.image) list.push(surface.image);
  if (surface.images) list.push(...surface.images);
  return list;
}

function Body({ children }: { children: React.ReactNode }) {
  return <div className="leaf__body">{children}</div>;
}

// ========================================================================
// L01 — Main sheet (canonical) with a renderable plate in a 3:4 side bay.
// ========================================================================

function L01Main({ leaf, activeFolderId }: LayoutProps) {
  const s = leaf.surface!;
  const left = (leaf.variant ?? "img-right") === "img-left";

  const context = (
    <>
      <StatusChip kind={s.surfaceType} /> Main sheet · <ImgBadge state={s.image.state} />
    </>
  );

  const refCol = (
    <div className="w-[36%] shrink-0 flex flex-col gap-3 min-h-0">
      <ImageZone
        image={s.image}
        className="w-full"
        description={s.descriptionSummary || s.sourceDescription}
        sourceName={s.sourceName}
      />
      <RightsBlock surface={s} />
      <SourceBlock surface={s} />
      <MembershipsBlock surface={s} activeFolderId={activeFolderId} />
      <ProvenanceLine surface={s} />
    </div>
  );
  const textCol = (
    <div className="flex-1 min-w-0 flex flex-col gap-3 overflow-hidden">
      <ScopeBlock surface={s} />
      <SourceTextBlock surface={s} />
      <div className="flex-1 min-h-0 overflow-hidden">
        <SpecTables tables={leaf.tables ?? []} columns={1} />
      </div>
    </div>
  );

  return (
    <Body>
      <LeafHead leaf={leaf} context={context} />
      <TitleBlock surface={s} />
      <div className="flex gap-6 flex-1 min-h-0 mt-3 overflow-hidden">
        {left ? (
          <>
            {refCol}
            {textCol}
          </>
        ) : (
          <>
            {textCol}
            {refCol}
          </>
        )}
      </div>
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L02 — Text sheet. No displayable image: a reading page (description +
// source text), with the six tables flowing onto appendix leaves.
// ========================================================================

function L02Text({ leaf, activeFolderId }: LayoutProps) {
  const s = leaf.surface!;
  return (
    <Body>
      <LeafHead
        leaf={leaf}
        context={
          <>
            <StatusChip kind={s.surfaceType} /> Text sheet · <ImgBadge state={s.image.state} />
          </>
        }
      />
      <TitleBlock surface={s} />
      <div className="mt-3 flex flex-col gap-3">
        <ScopeBlock surface={s} />
        <SourceTextBlock surface={s} />
      </div>
      <div className="grid grid-cols-3 gap-6 mt-4 pt-3 border-t border-line-soft">
        <RightsBlock surface={s} />
        <SourceBlock surface={s} />
        <MembershipsBlock surface={s} activeFolderId={activeFolderId} />
      </div>
      <div className="flex-1" />
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L03 — Plate dominant (only for renderable images), image in a 3:4 bay.
// ========================================================================

function L03Plate({ leaf, activeFolderId }: LayoutProps) {
  const s = leaf.surface!;
  return (
    <Body>
      <LeafHead
        leaf={leaf}
        context={
          <>
            <StatusChip kind={s.surfaceType} /> Plate · <ImgBadge state={s.image.state} />
          </>
        }
      />
      <div className="flex gap-6 flex-1 min-h-0 mt-3 overflow-hidden">
        <div className="w-[46%] shrink-0 min-h-0 flex items-start overflow-hidden">
          <ImageZone
            image={s.image}
            className="w-full"
            description={s.descriptionSummary || s.sourceDescription}
            sourceName={s.sourceName}
          />
        </div>
        <div className="flex-1 min-w-0 flex flex-col gap-2 overflow-hidden">
          <TitleBlock surface={s} size="md" />
          <ScopeBlock surface={s} />
          <div className="flex-1 min-h-0 overflow-hidden">
            <SpecTables tables={leaf.tables ?? []} columns={1} />
          </div>
          <RightsBlock surface={s} />
          <SourceBlock surface={s} />
          <MembershipsBlock surface={s} activeFolderId={activeFolderId} />
        </div>
      </div>
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L04 — Dual plate (two renderable photos on one page).
// ========================================================================

function L04Dual({ leaf, activeFolderId }: LayoutProps) {
  const s = leaf.surface!;
  const imgs = imagesOf(s)
    .filter((im) => isRenderableImage(im))
    .slice(0, 2);
  return (
    <Body>
      <LeafHead
        leaf={leaf}
        context={
          <>
            <StatusChip kind={s.surfaceType} /> Dual plate · <ImgBadge state={s.image.state} />
          </>
        }
      />
      <TitleBlock surface={s} size="md" />
      <div className="flex gap-6 mt-3" style={{ maxHeight: "50%" }}>
        {imgs.map((img, i) => (
          <div key={i} className="flex-1 min-w-0">
            <ImageZone image={img} className="w-full" sourceName={s.sourceName} />
          </div>
        ))}
      </div>
      <div className="mt-3"><ScopeBlock surface={s} /></div>
      <div className="flex-1 min-h-0 mt-2 overflow-hidden">
        <SpecTables tables={leaf.tables ?? []} columns={2} />
      </div>
      <div className="grid grid-cols-3 gap-6 mt-2 pt-2 border-t border-line-soft">
        <RightsBlock surface={s} />
        <SourceBlock surface={s} />
        <MembershipsBlock surface={s} activeFolderId={activeFolderId} />
      </div>
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L05 — Compound sheet (several weak records as one unit).
// ========================================================================

function L05Compound({ leaf, activeFolderId }: LayoutProps) {
  const s = leaf.surface!;
  const children = s.compoundChildren ?? [];
  return (
    <Body>
      <LeafHead
        leaf={leaf}
        context={
          <>
            <StatusChip kind={s.surfaceType} /> Compound unit · {children.length} records
          </>
        }
      />
      <TitleBlock surface={s} size="md" />
      <div className="flex-1 min-h-0 mt-3 overflow-hidden">
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          {children.map((c, i) => (
            <div key={i} className="border-t border-line-soft pt-1.5" style={{ fontSize: "0.64rem" }}>
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-bold">
                  {String(i + 1).padStart(2, "0")} · {c.title}
                </span>
                <ImgBadge state={c.imageState} />
              </div>
              <div className="text-ink-soft">
                {c.dateText} · {c.sourceName}
              </div>
              <p className="leading-snug mt-0.5">{c.note}</p>
              <a
                href={c.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="source-link mt-1"
                style={{ fontSize: "0.56rem" }}
              >
                Source ↗
              </a>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-2 pt-2 border-t border-line-soft">
        <MembershipsBlock surface={s} activeFolderId={activeFolderId} />
      </div>
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L06 — Sparse card (promotion / review status).
// ========================================================================

function L06Card({ leaf, activeFolderId }: LayoutProps) {
  const s = leaf.surface!;
  const reason = s.tables
    .find((t) => t.kind === "NORMALIZED")
    ?.rows.find(([l]) => /reason/i.test(l));
  return (
    <Body>
      <LeafHead
        leaf={leaf}
        context={
          <>
            <StatusChip kind={s.surfaceType} /> Sparse card · <ImgBadge state={s.image.state} />
          </>
        }
      />
      <TitleBlock surface={s} size="md" />
      <div className="mt-2" style={{ fontSize: "0.66rem" }}>
        <span className="label-caps text-ink-soft">promotion status</span>{" "}
        {s.rights.label}
        {reason ? (
          <span className="text-ink-soft"> · reason: {reason[1]}</span>
        ) : null}
        <span className="text-ink-soft">
          {" "}· completeness {s.completenessScore} (45–59 → card)
        </span>
      </div>
      <div className="flex gap-6 flex-1 min-h-0 mt-3 overflow-hidden">
        <div className="flex-1 min-w-0 overflow-hidden">
          <SpecTables tables={leaf.tables ?? []} columns={1} />
        </div>
        <div className="w-[36%] shrink-0 flex flex-col gap-3">
          <RightsBlock surface={s} />
          <SourceBlock surface={s} />
          <MembershipsBlock surface={s} activeFolderId={activeFolderId} />
        </div>
      </div>
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L07 — Fallback stub (deliberate "not ingested").
// ========================================================================

function L07Stub({ leaf, activeFolderId }: LayoutProps) {
  const s = leaf.surface!;
  const normalized = s.tables.find((t) => t.kind === "NORMALIZED");
  const reason = normalized?.rows.find(([l]) => /reason/i.test(l));
  const action = normalized?.rows.find(([l]) => /action/i.test(l));
  return (
    <Body>
      <LeafHead
        leaf={leaf}
        context={<>Fallback stub · not ingested · <ImgBadge state={s.image.state} /></>}
      />
      <TitleBlock surface={s} size="md" />
      <div className="flex gap-6 flex-1 min-h-0 mt-3 overflow-hidden">
        <div className="flex-1 min-w-0 flex flex-col gap-3 overflow-hidden">
          <dl className="deflist">
            <dt>status</dt>
            <dd>{s.rights.label}</dd>
            {reason ? (
              <>
                <dt>reason</dt>
                <dd>{reason[1]}</dd>
              </>
            ) : null}
            {action ? (
              <>
                <dt>next action</dt>
                <dd>{action[1]}</dd>
              </>
            ) : null}
            <dt>expected</dt>
            <dd>
              {s.image.state} · completeness {s.completenessScore} (25–44)
            </dd>
          </dl>
          <UncertaintyBlock surface={s} />
        </div>
        <div className="w-[40%] shrink-0 flex flex-col gap-3">
          <SourceBlock surface={s} />
          <MembershipsBlock surface={s} activeFolderId={activeFolderId} />
        </div>
      </div>
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L08 — Appendix / continuation (overflow tables only).
// ========================================================================

function L08Appendix({ leaf }: LayoutProps) {
  const s = leaf.surface!;
  return (
    <Body>
      <LeafHead leaf={leaf} context={<>Appendix · continuation</>} />
      <h2 className="leaf__title leaf__title--sm mt-3">{s.title}</h2>
      <p className="leaf__sub mt-1">Continuation of {s.provisionalDisplayNumber}</p>
      <div className="flex-1 min-h-0 mt-3 overflow-hidden">
        <SpecTables tables={leaf.tables ?? []} columns={1} />
      </div>
      <SheetMarkers leaf={leaf} />
    </Body>
  );
}

// ========================================================================
// L09 — Folder register / chronological index (clickable, multi-page).
// ========================================================================

function L09Register({ leaf, ctx }: LayoutProps) {
  const folder = leaf.folder!;
  const ft = getFolderType(folder.type);
  const groups = leaf.regGroups ?? [];
  const firstPage = (leaf.regPageNumber ?? 1) === 1;
  const map = ctx?.surfaceLeafIndex;

  return (
    <Body>
      <LeafHead
        leaf={leaf}
        swatch={<TypeSwatch type={folder.type} />}
        context={<>{ft?.label ?? folder.type} folder · register</>}
      />

      {firstPage ? (
        <header className="mt-3">
          <h1 className="leaf__title">{folder.title}</h1>
          <p className="leaf__sub mt-1.5">
            {dateSpanLabel(folder.dateStart, folder.dateEnd)} · members in
            chronological order
          </p>
          <p className="mt-2 col-justify" style={{ fontSize: "0.68rem", lineHeight: 1.5 }}>
            {folder.scopeNote}
          </p>
        </header>
      ) : (
        <p className="leaf__sub mt-3">{folder.title} · index continued</p>
      )}

      <div className="flex-1 min-h-0 mt-3 overflow-hidden">
        <div className="spec__label">
          <span className="k">Contents</span>
          <span className="sub">click a title to turn to its leaf</span>
        </div>
        <div className="mt-1">
          {groups.map((g) => (
            <div key={g.key} className="mb-2">
              <div className="flex items-baseline gap-2">
                <span className="font-bold" style={{ fontSize: "0.66rem" }}>
                  {g.label}
                </span>
                <span className="flex-1 border-b border-line-soft translate-y-[-0.18rem]" />
                <span className="label-caps text-ink-soft">{g.surfaces.length}</span>
              </div>
              {g.surfaces.map((su) => {
                const idx = map?.get(su.surfaceId);
                return (
                  <button
                    key={su.surfaceId}
                    type="button"
                    className="reg-row"
                    onClick={() => (idx != null ? ctx?.onJump?.(idx) : undefined)}
                  >
                    <span className="date">{su.dateText}</span>
                    <span className="title">{su.title}</span>
                    <span className="pg">
                      {idx != null ? `leaf ${idx + 1}` : ""}
                    </span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="sheet-markers">
        <span>L09.register</span>
        <span>{folder.folderId}</span>
        <span>index</span>
      </div>
    </Body>
  );
}

// ---- dispatch -----------------------------------------------------------

export function renderLeafContent(
  leaf: Leaf,
  activeFolderId?: string,
  ctx?: LeafCtx,
) {
  if (leaf.type === "register") return <L09Register leaf={leaf} ctx={ctx} />;
  if (leaf.type === "appendix") return <L08Appendix leaf={leaf} />;
  const props: LayoutProps = { leaf, activeFolderId, ctx };
  switch (leaf.layoutId) {
    case "L02.text":
      return <L02Text {...props} />;
    case "L03.plate":
      return <L03Plate {...props} />;
    case "L04.dual":
      return <L04Dual {...props} />;
    case "L05.compound":
      return <L05Compound {...props} />;
    case "L06.card":
      return <L06Card {...props} />;
    case "L07.stub":
      return <L07Stub {...props} />;
    case "L01.main":
    default:
      return <L01Main {...props} />;
  }
}

export { UncertaintyBlock };
