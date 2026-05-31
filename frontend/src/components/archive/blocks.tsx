import Link from "next/link";
import type { Surface, SurfaceTable } from "@/types/archive";
import { folderHref } from "@/lib/archive-data";
import { ImgBadge, Kicker, TypeSwatch } from "./primitives";

/**
 * Reusable slot blocks rendered as quiet, printed-manual typography (no chrome
 * boxes, no stamps). Layouts arrange these; the generator fills them from the
 * payload. Missing data leaves a reserved em-dash.
 */

const EM_DASH = "—";

function val(v: string | null | undefined): string {
  return v && v.trim() ? v : EM_DASH;
}

// ---- Title block --------------------------------------------------------

export function TitleBlock({
  surface,
  size = "lg",
}: {
  surface: Surface;
  size?: "lg" | "md";
}) {
  return (
    <header className="mt-3">
      <h1 className={size === "lg" ? "leaf__title" : "leaf__title leaf__title--sm"}>
        {surface.title}
      </h1>
      <p className="leaf__sub mt-1.5">
        {val(surface.dateText)}&nbsp;&nbsp;·&nbsp;&nbsp;{val(surface.objectType)}
        &nbsp;&nbsp;·&nbsp;&nbsp;{val(surface.medium)}
      </p>
      <p className="mt-0.5" style={{ fontSize: "0.66rem" }}>
        <Kicker>creator</Kicker>{" "}
        <span className="ml-1">{val(surface.creator)}</span>
        <span className="mx-2 text-line-soft" aria-hidden>
          /
        </span>
        <Kicker>place</Kicker>{" "}
        <span className="ml-1">{val(surface.placeText)}</span>
      </p>
    </header>
  );
}

// ---- Scope / lead -------------------------------------------------------

export function ScopeBlock({ surface }: { surface: Surface }) {
  const text =
    surface.descriptionSummary ||
    surface.sourceDescription ||
    surface.sourceNotes ||
    "";
  if (!text) return null;
  return (
    <p
      className="col-justify text-ink"
      style={{ fontSize: "0.7rem", lineHeight: 1.55 }}
    >
      {text}
    </p>
  );
}

function subjectsText(raw?: string): string {
  if (!raw) return "";
  const titles = [...raw.matchAll(/"title":\s*"([^"]+)"/g)].map((m) => m[1]);
  if (titles.length) return titles.join(" · ");
  return raw.replace(/\s*;\s*/g, " · ").trim();
}

/** Source-side text (extra description + notes + subjects) for text pages. */
export function SourceTextBlock({ surface }: { surface: Surface }) {
  const summary = surface.descriptionSummary?.trim();
  const desc = surface.sourceDescription?.trim();
  const rawNotes = surface.sourceNotes?.trim();
  const subjects = subjectsText(surface.sourceSubjects);
  const context = surface.historicalContextNote?.trim();
  const classification = surface.classificationRationale?.trim();
  const uncertainty = surface.uncertaintyNote?.trim();
  const citation = surface.citationBasis?.trim();
  // The lead paragraph already shows summary || desc; never repeat it here.
  const lead = summary || desc;
  const showDesc = desc && desc !== summary && desc !== lead;
  const notes = rawNotes && rawNotes !== lead && rawNotes !== desc ? rawNotes : "";
  if (!showDesc && !notes && !subjects && !context && !classification && !uncertainty && !citation) return null;
  return (
    <div>
      <div className="spec__label">
        <span className="k">Source text</span>
        <span className="sub">captured + normalized notes</span>
      </div>
      {showDesc ? (
        <p className="col-justify" style={{ fontSize: "0.64rem", lineHeight: 1.5 }}>
          {desc}
        </p>
      ) : null}
      {notes ? (
        <p
          className="col-justify text-ink-soft mt-1"
          style={{ fontSize: "0.6rem", lineHeight: 1.5 }}
        >
          {notes}
        </p>
      ) : null}
      {subjects ? (
        <p className="mt-1" style={{ fontSize: "0.6rem" }}>
          <span className="label-caps text-ink-soft">subjects</span> {subjects}
        </p>
      ) : null}
      {context ? (
        <p className="col-justify mt-2" style={{ fontSize: "0.6rem", lineHeight: 1.5 }}>
          <span className="label-caps text-ink-soft">context</span> {context}
        </p>
      ) : null}
      {classification ? (
        <p className="col-justify mt-1 text-ink-soft" style={{ fontSize: "0.58rem", lineHeight: 1.45 }}>
          <span className="label-caps">classification</span> {classification}
        </p>
      ) : null}
      {uncertainty ? (
        <p className="col-justify mt-1 text-ink-soft" style={{ fontSize: "0.58rem", lineHeight: 1.45 }}>
          <span className="label-caps">uncertainty</span> {uncertainty}
        </p>
      ) : null}
      {citation ? (
        <p className="mt-1 break-words text-ink-soft" style={{ fontSize: "0.56rem", lineHeight: 1.4 }}>
          <span className="label-caps">citation basis</span> {citation}
        </p>
      ) : null}
    </div>
  );
}

// ---- Spec sections (the six tables) ------------------------------------

const VISUAL_PREDICATES = new Set(["visually_resembles"]);

function isUrl(v: string) {
  return /^https?:\/\//i.test(v);
}

const TABLE_SUBTITLE: Record<string, string> = {
  SOURCE: "as found",
  NORMALIZED: "normalized",
  RIGHTS: "display state",
  CLASSIFICATION: "authority",
  RELATIONS: "relations",
  CITATIONS: "citations",
};

export function SpecTable({ table }: { table: SurfaceTable }) {
  return (
    <section className="spec">
      <div className="spec__label">
        <span className="k">{table.kind}</span>
        <span className="sub">{TABLE_SUBTITLE[table.kind] ?? ""}</span>
      </div>
      <table>
        <tbody>
          {table.rows.map(([label, value], i) => {
            const visual =
              table.kind === "RELATIONS" && VISUAL_PREDICATES.has(label);
            return (
              <tr key={`${label}-${i}`}>
                <th>
                  {label}
                  {visual ? (
                    <span className="ml-1 text-ink-soft">(visual only)</span>
                  ) : null}
                </th>
                <td>
                  {isUrl(value) ? (
                    <a
                      href={value}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline break-all"
                    >
                      {value}
                    </a>
                  ) : (
                    value
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

export function SpecTables({
  tables,
  columns = 1,
}: {
  tables: SurfaceTable[];
  columns?: 1 | 2 | 3;
}) {
  if (tables.length === 0) return null;
  const colClass =
    columns === 3
      ? "[column-count:3]"
      : columns === 2
        ? "[column-count:2]"
        : "";
  return (
    <div className={`min-h-0 ${colClass} [column-gap:1.6rem]`}>
      {tables.map((t) => (
        <div key={t.kind} className="mb-2.5 break-inside-avoid">
          <SpecTable table={t} />
        </div>
      ))}
    </div>
  );
}

// ---- Rights & display ---------------------------------------------------

export function RightsBlock({ surface }: { surface: Surface }) {
  const { image, rights, reviewGates } = surface;
  return (
    <div>
      <div className="spec__label">
        <span className="k">Rights</span>
        <span className="sub">{image.state}</span>
      </div>
      <dl className="deflist">
        <dt>policy</dt>
        <dd>{rights.displayPolicy}</dd>
        <dt>state</dt>
        <dd>{rights.state}</dd>
        <dt>local copy</dt>
        <dd>no</dd>
        <dt>review</dt>
        <dd>{reviewGates.rightsReviewed ? "reviewed" : "required"}</dd>
      </dl>
      {image.licenseLabel ? (
        <p
          className="mt-1 text-ink-soft leading-snug"
          style={{ fontSize: "0.58rem" }}
        >
          {image.licenseLabel}
        </p>
      ) : null}
    </div>
  );
}

// ---- Source -------------------------------------------------------------

export function SourceBlock({ surface }: { surface: Surface }) {
  return (
    <div>
      <div className="spec__label">
        <span className="k">Source</span>
        <span className="sub">return</span>
      </div>
      <dl className="deflist">
        <dt>holder</dt>
        <dd>{val(surface.sourceName)}</dd>
        <dt>accessed</dt>
        <dd>{val(surface.accessDate)}</dd>
      </dl>
      <a
        href={surface.sourceUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="source-link mt-1.5"
        style={{ fontSize: "0.62rem" }}
      >
        View at source ↗
      </a>
    </div>
  );
}

// ---- Folder memberships -------------------------------------------------

export function MembershipsBlock({
  surface,
  activeFolderId,
}: {
  surface: Surface;
  activeFolderId?: string;
}) {
  return (
    <div>
      <div className="spec__label">
        <span className="k">Folders</span>
        <span className="sub">filter views</span>
      </div>
      <ul className="space-y-0.5" style={{ fontSize: "0.66rem" }}>
        {surface.folders.map((f) => {
          const href = folderHref(f.folderId);
          const active = f.folderId === activeFolderId;
          const inner = (
            <span
              className={`inline-flex items-center gap-1.5 ${active ? "font-bold" : ""}`}
            >
              <TypeSwatch type={f.type} />
              <span className={href ? "underline" : ""}>{f.title}</span>
            </span>
          );
          return (
            <li key={f.folderId}>
              {href ? (
                <Link href={href} className="hover:opacity-80">
                  {inner}
                </Link>
              ) : (
                inner
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ---- Provenance line ----------------------------------------------------

export function ProvenanceLine({ surface }: { surface: Surface }) {
  const hn = surface.historicalNodeIds ?? [];
  const mv = surface.movementIds ?? [];
  if (hn.length === 0 && mv.length === 0) return null;
  return (
    <p className="text-ink-soft" style={{ fontSize: "0.56rem" }}>
      <Kicker>provenance</Kicker>{" "}
      {hn.length > 0 ? `HN ${hn.join(", ")}` : null}
      {hn.length > 0 && mv.length > 0 ? " · " : null}
      {mv.length > 0 ? `MV ${mv.join(", ")}` : null}
    </p>
  );
}

// ---- Uncertainty --------------------------------------------------------

export function UncertaintyBlock({ surface }: { surface: Surface }) {
  const notes: string[] = [];
  if (/\/|c\.|circa|undated/i.test(surface.dateText)) {
    notes.push("Date is approximate or spans a range.");
  }
  if (!surface.reviewGates.rightsReviewed) {
    notes.push("Item-level rights not yet reviewed.");
  }
  if (surface.surfaceType === "fallback_stub") {
    notes.push("Fallback stub — not an ingested source record.");
  }
  if (notes.length === 0) return null;
  return (
    <div>
      <div className="spec__label">
        <span className="k">Uncertainty</span>
      </div>
      <ul
        className="list-disc list-inside leading-snug text-ink-soft"
        style={{ fontSize: "0.6rem" }}
      >
        {notes.map((n) => (
          <li key={n}>{n}</li>
        ))}
      </ul>
    </div>
  );
}

export { ImgBadge };
