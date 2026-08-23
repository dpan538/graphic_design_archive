import {
  makeMissingness,
  prepareProjectionBase,
  stableUnique,
  assertPublicArchiveRefs,
  type TraceAccessibleRow,
} from "../domain";
import type { TraceSourcesDataset, TraceSourcesInput } from "./types";

function label(value: { stableId: string; label?: string }): string {
  return value.label?.trim() || value.stableId;
}

export function deriveSourcesTraceDataset(input: TraceSourcesInput): TraceSourcesDataset {
  const base = prepareProjectionBase(input);
  const sourceItems = stableUnique(input.sourceItems, (item) => item.id);
  const sourceAssociations = stableUnique(input.sourceAssociations, (item) => item.id);
  const sourceLinks = stableUnique(input.sourceLinks, (item) => item.id);
  assertPublicArchiveRefs(
    [
      ...sourceItems.map((item) => item.ref),
      ...sourceAssociations.flatMap((item) => [item.object, item.sourceRecord]),
      ...sourceLinks.flatMap((item) => [item.from, item.to]),
    ],
    base.publicObjectStableIds,
  );
  const missingness = makeMissingness(input.denominator, base.unknowns.length, 0);
  const counts = Object.freeze({
    itemCount: sourceItems.length + 1,
    semanticEdgeCount: base.semanticEdges.length,
    nonSemanticAssociationCount: sourceAssociations.length + sourceLinks.length,
    denominator: input.denominator,
  });
  const datasetWithoutRows = {
    domain: "sources" as const,
    release: base.release,
    availability: base.availability,
    selectedRecord: Object.freeze({ ...input.selectedRecord }),
    sourceItems,
    sourceAssociations,
    sourceLinks,
    semanticEdges: base.semanticEdges,
    unknowns: base.unknowns,
    missingness,
    counts,
    warnings: base.warnings,
  };
  return Object.freeze({
    ...datasetWithoutRows,
    accessibleRows: toSourcesAccessibleRows(datasetWithoutRows),
  });
}

export function toSourcesAccessibleRows(
  dataset: Omit<TraceSourcesDataset, "accessibleRows"> | TraceSourcesDataset,
): readonly TraceAccessibleRow[] {
  const rows: TraceAccessibleRow[] = [
    ...dataset.sourceItems.map((item) => ({
      id: `item:${item.id}`,
      category: item.kind,
      label: label(item.ref),
      values: Object.freeze([
        { label: "Kind", value: item.kind },
        { label: "Evidence references", value: String(item.evidenceRefs.length) },
      ]),
    })),
    ...dataset.sourceAssociations.map((item) => ({
      id: `association:${item.id}`,
      category: "source_association",
      label: `${label(item.object)} — ${item.associationType} — ${label(item.sourceRecord)}`,
      values: Object.freeze([{ label: "Inference", value: "none; association is not semantic support" }]),
    })),
    ...dataset.sourceLinks.map((item) => ({
      id: `link:${item.id}`,
      category: item.kind,
      label: `${label(item.from)} — ${item.kind} — ${label(item.to)}`,
      values: Object.freeze([
        { label: "Evidence references", value: String(item.evidenceRefs.length) },
        { label: "Inference", value: "preserve explicit link role only" },
      ]),
    })),
    ...dataset.semanticEdges.map((item) => ({
      id: `semantic:${item.id}`,
      category: "accepted_semantic_edge",
      label: `${label(item.subject)} — ${item.predicateId} — ${label(item.object)}`,
      values: Object.freeze([{ label: "Evidence references", value: String(item.evidenceRefs.length) }]),
    })),
  ];
  return stableUnique(rows, (row) => row.id);
}
