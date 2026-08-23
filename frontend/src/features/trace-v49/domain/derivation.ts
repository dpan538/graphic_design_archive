import type { TraceAvailabilityState } from "./availability";
import type { TracePredicateDefinition } from "./evidence";
import type { TracePublicDataRef } from "./identity";
import type { TraceSemanticEdge } from "./relation";
import type { TraceReleaseRef } from "./release";
import { copyAvailability } from "./availability";
import { assertPublicArchiveRefs } from "./identity";
import { assertAcceptedSemanticEdge } from "./relation";
import { assertTraceReleaseRef } from "./release";

export interface TraceUnknown {
  readonly field: string;
  readonly reason: string;
}

export interface TraceMissingness {
  readonly denominator: number;
  readonly unknownCount: number;
  readonly unmappedCount: number;
}

export interface TraceDatasetCounts {
  readonly itemCount: number;
  readonly semanticEdgeCount: number;
  readonly nonSemanticAssociationCount: number;
  readonly denominator: number;
}

export interface TraceAccessibleRow {
  readonly id: string;
  readonly category: string;
  readonly label: string;
  readonly values: readonly Readonly<{ label: string; value: string }>[];
}

export interface TraceProjectionBaseInput {
  readonly release: TraceReleaseRef;
  readonly publicObjectStableIds: readonly string[];
  readonly availability: TraceAvailabilityState;
  readonly selectedRecord: TracePublicDataRef;
  readonly predicateRegistry: readonly TracePredicateDefinition[];
  readonly semanticEdges: readonly TraceSemanticEdge[];
  readonly unknowns: readonly TraceUnknown[];
  readonly warnings: readonly string[];
  readonly denominator: number;
}

export function prepareProjectionBase(input: TraceProjectionBaseInput): {
  release: TraceReleaseRef;
  availability: TraceAvailabilityState;
  predicates: ReadonlyMap<string, TracePredicateDefinition>;
  semanticEdges: readonly TraceSemanticEdge[];
  unknowns: readonly TraceUnknown[];
  warnings: readonly string[];
  publicObjectStableIds: ReadonlySet<string>;
} {
  assertTraceReleaseRef(input.release);
  if (!Number.isSafeInteger(input.denominator) || input.denominator < 0) {
    throw new Error("TRACE denominator must be a non-negative safe integer");
  }
  if (input.selectedRecord.kind !== "archive_object") {
    throw new Error("TRACE selected record must be an archive object");
  }
  const publicObjectStableIds = new Set(input.publicObjectStableIds);
  if (publicObjectStableIds.size !== input.publicObjectStableIds.length) {
    throw new Error("duplicate public archive object stable ID");
  }
  assertPublicArchiveRefs([input.selectedRecord], publicObjectStableIds);
  const predicateDefinitions = stableUnique(
    input.predicateRegistry,
    (item) => item.predicateId,
  );
  const predicates = new Map(predicateDefinitions.map((item) => [item.predicateId, item]));
  const semanticEdges = stableUnique(
    input.semanticEdges,
    (item) => item.id,
    (item) => JSON.stringify([
      item.predicateId, item.subject.kind, item.subject.stableId,
      item.object.kind, item.object.stableId,
      item.evidenceRefs.map((evidence) => [evidence.kind, evidence.stableId, evidence.locatorAvailable]),
    ]),
  );
  for (const edge of semanticEdges) {
    assertPublicArchiveRefs([edge.subject, edge.object], publicObjectStableIds);
    assertAcceptedSemanticEdge(edge, predicates);
  }
  return {
    release: Object.freeze({ ...input.release }),
    availability: copyAvailability(input.availability),
    predicates,
    semanticEdges,
    unknowns: stableUnique(input.unknowns, (item) => `${item.field}\u0000${item.reason}`),
    warnings: Object.freeze([...new Set(input.warnings)].sort(compareText)),
    publicObjectStableIds,
  };
}

export function stableUnique<T>(
  values: readonly T[],
  identity: (value: T) => string,
  fingerprint: (value: T) => string = (value) => JSON.stringify(value),
): readonly T[] {
  const seen = new Map<string, string>();
  const kept: T[] = [];
  for (const value of values) {
    const key = identity(value);
    const nextFingerprint = fingerprint(value);
    const prior = seen.get(key);
    if (prior === undefined) {
      seen.set(key, nextFingerprint);
      kept.push(value);
    } else if (prior !== nextFingerprint) {
      throw new Error(`conflicting TRACE identity: ${key}`);
    }
  }
  return Object.freeze(kept.sort((left, right) => compareText(identity(left), identity(right))));
}

export function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

export function collectItems(values: readonly TracePublicDataRef[]): readonly TracePublicDataRef[] {
  return stableUnique(values, (item) => `${item.kind}\u0000${item.stableId}`);
}

export function makeMissingness(
  denominator: number,
  unknownCount: number,
  unmappedCount: number,
): TraceMissingness {
  for (const value of [denominator, unknownCount, unmappedCount]) {
    if (!Number.isSafeInteger(value) || value < 0) throw new Error("invalid TRACE missingness count");
  }
  if (unknownCount > denominator || unmappedCount > denominator) {
    throw new Error("TRACE missingness cannot exceed its denominator");
  }
  return Object.freeze({ denominator, unknownCount, unmappedCount });
}
