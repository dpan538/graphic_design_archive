import {
  makeMissingness,
  prepareProjectionBase,
  stableUnique,
  assertPublicArchiveRefs,
  type TraceAccessibleRow,
} from "../domain";
import type {
  TraceAggregate,
  TracePlaceObservation,
  TraceSpacetimeDataset,
  TraceSpacetimeInput,
  TraceTimeObservation,
} from "./types";

function validateAggregate(aggregate: TraceAggregate): TraceAggregate {
  for (const value of [aggregate.visibleCount, aggregate.denominator, aggregate.unknownCount, aggregate.unmappedCount]) {
    if (!Number.isSafeInteger(value) || value < 0) throw new Error("invalid TRACE aggregate count");
  }
  if (aggregate.visibleCount + aggregate.unknownCount > aggregate.denominator) {
    throw new Error("TRACE visible + unknown exceeds denominator");
  }
  if (aggregate.unmappedCount > aggregate.denominator) throw new Error("TRACE unmapped exceeds denominator");
  return Object.freeze({ ...aggregate });
}

function validatePlace(item: TracePlaceObservation): TracePlaceObservation {
  if (item.precision === "unknown" && item.coordinates) throw new Error("unknown TRACE place cannot have coordinates");
  if (item.coordinates) {
    const { latitude, longitude } = item.coordinates;
    if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
      throw new Error(`invalid TRACE coordinates: ${item.id}`);
    }
  }
  return item;
}

function validateTime(item: TraceTimeObservation): TraceTimeObservation {
  if (item.precision === "unknown" && (item.start !== undefined || item.end !== undefined)) {
    throw new Error("unknown TRACE time cannot have start/end values");
  }
  if (item.precision === "range" && (!item.start || !item.end)) {
    throw new Error("TRACE time range requires start and end");
  }
  return item;
}

export function deriveSpacetimeTraceDataset(input: TraceSpacetimeInput): TraceSpacetimeDataset {
  const base = prepareProjectionBase(input);
  const places = stableUnique(input.places.map(validatePlace), (item) => item.id);
  const times = stableUnique(input.times.map(validateTime), (item) => item.id);
  assertPublicArchiveRefs(
    [...places.map((item) => item.place), ...times.map((item) => item.time)],
    base.publicObjectStableIds,
  );
  const aggregate = validateAggregate(input.aggregate);
  if (aggregate.denominator !== input.denominator) throw new Error("TRACE aggregate denominator mismatch");
  const missingness = makeMissingness(input.denominator, aggregate.unknownCount, aggregate.unmappedCount);
  const counts = Object.freeze({
    itemCount: places.length + times.length + 1,
    semanticEdgeCount: base.semanticEdges.length,
    nonSemanticAssociationCount: places.length + times.length,
    denominator: input.denominator,
  });
  const datasetWithoutRows = {
    domain: "spacetime" as const,
    release: base.release,
    availability: base.availability,
    selectedRecord: Object.freeze({ ...input.selectedRecord }),
    places,
    times,
    semanticEdges: base.semanticEdges,
    unknowns: base.unknowns,
    aggregate,
    missingness,
    counts,
    warnings: base.warnings,
  };
  return Object.freeze({
    ...datasetWithoutRows,
    accessibleRows: toSpacetimeAccessibleRows(datasetWithoutRows),
  });
}

export function toSpacetimeAccessibleRows(
  dataset: Omit<TraceSpacetimeDataset, "accessibleRows"> | TraceSpacetimeDataset,
): readonly TraceAccessibleRow[] {
  const rows: TraceAccessibleRow[] = [
    ...dataset.places.map((item) => ({
      id: `place:${item.id}`,
      category: "place_observation",
      label: item.place.label?.trim() || item.place.stableId,
      values: Object.freeze([
        { label: "Role", value: item.role },
        { label: "Precision", value: item.precision },
        { label: "Coordinates", value: item.coordinates ? `${item.coordinates.latitude}, ${item.coordinates.longitude}` : "unmapped" },
        { label: "Coordinate provenance", value: item.coordinates?.provenance ?? "none" },
      ]),
    })),
    ...dataset.times.map((item) => ({
      id: `time:${item.id}`,
      category: "time_observation",
      label: item.time.label?.trim() || item.time.stableId,
      values: Object.freeze([
        { label: "Role", value: item.role },
        { label: "Precision", value: item.precision },
        { label: "Start", value: item.start ?? "unknown" },
        { label: "End", value: item.end ?? "unknown" },
      ]),
    })),
    {
      id: "aggregate:spacetime",
      category: "aggregate",
      label: "Spacetime coverage",
      values: Object.freeze([
        { label: "Visible", value: String(dataset.aggregate.visibleCount) },
        { label: "Denominator", value: String(dataset.aggregate.denominator) },
        { label: "Unknown", value: String(dataset.aggregate.unknownCount) },
        { label: "Unmapped", value: String(dataset.aggregate.unmappedCount) },
      ]),
    },
  ];
  return stableUnique(rows, (row) => row.id);
}
