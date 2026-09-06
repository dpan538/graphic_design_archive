/* Context Canvas — the presentation model (§7g): ONE description of what
   the page shows, read three ways — the canvas's fields and chips, the
   accessible rows, and the clipboard tables. The object (title; date;
   attribution; type; source; stable ID), the three dimensions in the
   governed order with the object's terms of each kind and whether each
   is on the canvas, the one interpretation boundary, a short footer.
   Nothing here adds meaning: it restates the governed representations
   and the selected record's source-reported fields. */

import {
  contextCanvasEntityId,
  type ContextCanvasGovernedRepresentation,
} from "@/features/trace-v49/context/canvas/types";
import { KINDS, type ContextKind } from "./content";

export interface PresentedObject {
  readonly title: string;
  readonly stableId: string;
  readonly dateDisplay?: string;
  readonly creatorAttribution?: string;
  readonly objectType?: string;
  readonly sourceName?: string;
}

export interface PresentedTerm {
  readonly entityId: string;
  readonly termId: string;
  readonly label: string;
  readonly kind: ContextKind;
  readonly visible: boolean;
  readonly representation: ContextCanvasGovernedRepresentation;
}

export interface PresentedDimension {
  readonly kind: ContextKind;
  readonly word: string;
  readonly items: readonly PresentedTerm[];
}

export interface ContextPresentation {
  readonly object: PresentedObject;
  readonly dimensions: readonly PresentedDimension[];
  readonly boundary: string;
  readonly footer: string;
}

export const termEntityId = (termId: string) => contextCanvasEntityId({ stableId: termId, kind: "controlled_term" });

/* "v49-api-contract-fresh-c" → "v49": the release's short name for
   reader-facing copy; the full identity stays in the technical copy */
export function shortRelease(releaseId: string): string {
  return /^v\d+/u.exec(releaseId)?.[0] ?? releaseId;
}

export function buildPresentation(input: Readonly<{
  object: PresentedObject;
  representations: readonly ContextCanvasGovernedRepresentation[];
  visibleIds: ReadonlySet<string>;
  boundary: string;
  releaseId: string;
  canvasName: string;
}>): ContextPresentation {
  return Object.freeze({
    object: input.object,
    dimensions: Object.freeze(KINDS.map(({ kind, word }) => Object.freeze({
      kind,
      word,
      items: Object.freeze(input.representations
        .filter((r) => r.kind === kind)
        .map((r) => {
          const entityId = termEntityId(r.termId);
          return Object.freeze({
            entityId,
            termId: r.termId,
            label: r.label,
            kind,
            visible: input.visibleIds.has(entityId),
            representation: r,
          });
        })),
    }))),
    boundary: input.boundary,
    footer: `MGDA · ${shortRelease(input.releaseId)} · ${input.canvasName}`,
  });
}

/* the object's fields, in the order the sheet prints them; empty ones
   are omitted, never invented */
function objectFields(object: PresentedObject): readonly Readonly<{ field: string; value: string }>[] {
  const rows = [
    { field: "Title", value: object.title.trim() || object.stableId },
    { field: "Date", value: object.dateDisplay ?? "" },
    { field: "Attribution", value: object.creatorAttribution ?? "" },
    { field: "Type", value: object.objectType ?? "" },
    { field: "Source", value: object.sourceName ?? "" },
    { field: "ID", value: object.stableId },
  ];
  return rows.filter((row) => row.value.trim());
}

/* the context rows: one per term on the canvas, the dimension repeated;
   a dimension with nothing on the canvas is one row, "Not recorded" or
   "n set aside" */
function contextRows(
  presentation: ContextPresentation,
  notRecorded: string,
  setAside: (n: number) => string,
): readonly Readonly<{ dimension: string; context: string }>[] {
  return presentation.dimensions.flatMap((dimension) => {
    const shown = dimension.items.filter((item) => item.visible);
    if (shown.length > 0) return shown.map((item) => ({ dimension: dimension.word, context: item.label }));
    return [{
      dimension: dimension.word,
      context: dimension.items.length > 0 ? setAside(dimension.items.length) : notRecorded,
    }];
  });
}

const mdCell = (value: string) => value.replace(/\|/g, "\\|").replace(/\s+/g, " ").trim();

export function presentationAsMarkdown(
  presentation: ContextPresentation,
  notRecorded: string,
  setAside: (n: number) => string,
  canvasName: string,
  archiveName: string,
): string {
  const lines = [
    `# ${canvasName} — ${archiveName}`,
    "",
    "## Object",
    "",
    "| Field | Value |",
    "|---|---|",
    ...objectFields(presentation.object).map((row) => `| ${mdCell(row.field)} | ${mdCell(row.value)} |`),
    "",
    "## Context",
    "",
    "| Dimension | Context |",
    "|---|---|",
    ...contextRows(presentation, notRecorded, setAside).map((row) => `| ${mdCell(row.dimension)} | ${mdCell(row.context)} |`),
    "",
    presentation.boundary,
    "",
    presentation.footer,
    "",
  ];
  return lines.join("\n");
}

const escapeHtml = (value: string) => value
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");

export function presentationAsHtml(
  presentation: ContextPresentation,
  notRecorded: string,
  setAside: (n: number) => string,
  canvasName: string,
  archiveName: string,
): string {
  const table = (head: readonly [string, string], rows: readonly Readonly<{ a: string; b: string }>[]) => [
    "<table>",
    `<thead><tr><th>${escapeHtml(head[0])}</th><th>${escapeHtml(head[1])}</th></tr></thead>`,
    "<tbody>",
    ...rows.map((row) => `<tr><td>${escapeHtml(row.a)}</td><td>${escapeHtml(row.b)}</td></tr>`),
    "</tbody>",
    "</table>",
  ].join("");
  return [
    `<h1>${escapeHtml(canvasName)} — ${escapeHtml(archiveName)}</h1>`,
    "<h2>Object</h2>",
    table(["Field", "Value"], objectFields(presentation.object).map((row) => ({ a: row.field, b: row.value }))),
    "<h2>Context</h2>",
    table(["Dimension", "Context"], contextRows(presentation, notRecorded, setAside).map((row) => ({ a: row.dimension, b: row.context }))),
    `<p>${escapeHtml(presentation.boundary)}</p>`,
    `<p>${escapeHtml(presentation.footer)}</p>`,
  ].join("\n");
}
