import {
  collectItems,
  assertPublicArchiveRefs,
  makeMissingness,
  prepareProjectionBase,
  stableUnique,
  type TraceAccessibleRow,
} from "../domain";
import type { TraceContextDataset, TraceContextInput } from "./types";

function label(value: { stableId: string; label?: string }): string {
  return value.label?.trim() || value.stableId;
}

export function deriveContextTraceDataset(input: TraceContextInput): TraceContextDataset {
  const base = prepareProjectionBase(input);
  const controlledAssignments = stableUnique(input.controlledAssignments, (item) => item.id);
  const curatedMemberships = stableUnique(input.curatedMemberships, (item) => item.id);
  assertPublicArchiveRefs(
    [
      ...controlledAssignments.flatMap((item) => [item.subject, item.value]),
      ...curatedMemberships.flatMap((item) => [item.member, item.container]),
    ],
    base.publicObjectStableIds,
  );
  const items = collectItems([
    input.selectedRecord,
    ...controlledAssignments.flatMap((item) => [item.subject, item.value]),
    ...curatedMemberships.flatMap((item) => [item.member, item.container]),
    ...base.semanticEdges.flatMap((item) => [item.subject, item.object]),
  ]);
  const missingness = makeMissingness(input.denominator, base.unknowns.length, 0);
  const counts = Object.freeze({
    itemCount: items.length,
    semanticEdgeCount: base.semanticEdges.length,
    nonSemanticAssociationCount: controlledAssignments.length + curatedMemberships.length,
    denominator: input.denominator,
  });
  const datasetWithoutRows = {
    domain: "context" as const,
    release: base.release,
    availability: base.availability,
    selectedRecord: Object.freeze({ ...input.selectedRecord }),
    items,
    controlledAssignments,
    curatedMemberships,
    semanticEdges: base.semanticEdges,
    unknowns: base.unknowns,
    missingness,
    counts,
    warnings: base.warnings,
  };
  return Object.freeze({
    ...datasetWithoutRows,
    accessibleRows: toContextAccessibleRows(datasetWithoutRows),
  });
}

export function toContextAccessibleRows(
  dataset: Omit<TraceContextDataset, "accessibleRows"> | TraceContextDataset,
): readonly TraceAccessibleRow[] {
  const rows: TraceAccessibleRow[] = [
    {
      id: `selected:${dataset.selectedRecord.stableId}`,
      category: "selected_record",
      label: label(dataset.selectedRecord),
      values: Object.freeze([{ label: "Stable ID", value: dataset.selectedRecord.stableId }]),
    },
    ...dataset.controlledAssignments.map((item) => ({
      id: `assignment:${item.id}`,
      category: "controlled_assignment",
      label: `${label(item.subject)} — ${item.assignmentType} — ${label(item.value)}`,
      values: Object.freeze([
        { label: "State", value: item.state },
        { label: "Association class", value: "controlled assignment; not a semantic relation" },
      ]),
    })),
    ...dataset.curatedMemberships.map((item) => ({
      id: `membership:${item.id}`,
      category: "curated_membership",
      label: `${label(item.member)} — ${item.membershipType} — ${label(item.container)}`,
      values: Object.freeze([
        { label: "State", value: item.state },
        { label: "Association class", value: "curated membership; not a semantic relation" },
      ]),
    })),
    ...dataset.semanticEdges.map((item) => ({
      id: `semantic:${item.id}`,
      category: "accepted_semantic_edge",
      label: `${label(item.subject)} — ${item.predicateId} — ${label(item.object)}`,
      values: Object.freeze([
        { label: "Evidence references", value: String(item.evidenceRefs.length) },
        { label: "State", value: item.status },
      ]),
    })),
  ];
  return stableUnique(rows, (row) => row.id);
}
