import type {
  TraceContextInput,
  TraceSourcesInput,
  TraceSpacetimeInput,
} from "../index";

// These two IDs are in the sealed 7,995-object v49 public cohort. The fixture
// deliberately contains no title, URL, evidence wording, UUID, or held row.
export const TRACE_PUBLIC_FIXTURE_OBJECT_IDS = Object.freeze([
  "SURF-AICTRACEV47R0001",
  "SURF-AICTRACEV47R0002",
]);

export const TRACE_V49_FIXTURE_RELEASE = Object.freeze({
  releaseId: "v49-api-contract-fresh-c",
  manifestSha256: "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a",
});

const selectedRecord = Object.freeze({
  stableId: TRACE_PUBLIC_FIXTURE_OBJECT_IDS[0],
  kind: "archive_object" as const,
});

const base = Object.freeze({
  release: TRACE_V49_FIXTURE_RELEASE,
  publicObjectStableIds: TRACE_PUBLIC_FIXTURE_OBJECT_IDS,
  availability: Object.freeze({
    state: "not_published" as const,
    reasonCodes: Object.freeze(["TRACE_V49_PUBLIC_DATASET_EMPTY"]),
    message: "Synthetic preprogram fixture; not a v49 public data projection.",
  }),
  selectedRecord,
  predicateRegistry: Object.freeze([]),
  semanticEdges: Object.freeze([]),
  unknowns: Object.freeze([]),
  warnings: Object.freeze(["SYNTHETIC_FIXTURE_ONLY"]),
  denominator: 2,
});

export const TRACE_PUBLIC_CONTEXT_FIXTURE: TraceContextInput = Object.freeze({
  ...base,
  controlledAssignments: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-ASSIGNMENT-002",
      connectionKind: "controlled_assignment" as const,
      subject: selectedRecord,
      value: Object.freeze({ stableId: "SYNTHETIC-CONTEXT-002", kind: "controlled_term" as const }),
      assignmentType: "object_type",
      state: "proposed" as const,
    }),
    Object.freeze({
      id: "SYNTHETIC-ASSIGNMENT-001",
      connectionKind: "controlled_assignment" as const,
      subject: selectedRecord,
      value: Object.freeze({ stableId: "SYNTHETIC-CONTEXT-001", kind: "controlled_term" as const }),
      assignmentType: "medium",
      state: "proposed" as const,
    }),
  ]),
  curatedMemberships: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-MEMBERSHIP-001",
      connectionKind: "curated_membership" as const,
      member: selectedRecord,
      container: Object.freeze({ stableId: "SYNTHETIC-FOLDER-001", kind: "controlled_term" as const }),
      membershipType: "folder_membership",
      state: "proposed" as const,
    }),
  ]),
});

export const TRACE_PUBLIC_SPACETIME_FIXTURE: TraceSpacetimeInput = Object.freeze({
  ...base,
  places: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-PLACE-OBSERVATION-001",
      place: Object.freeze({ stableId: "SYNTHETIC-PLACE-APPROXIMATE", kind: "place" as const }),
      role: "broad_region" as const,
      precision: "approximate" as const,
      evidenceRefs: Object.freeze([]),
    }),
    Object.freeze({
      id: "SYNTHETIC-PLACE-OBSERVATION-002",
      place: Object.freeze({ stableId: "SYNTHETIC-PLACE-UNKNOWN", kind: "place" as const }),
      role: "unspecified" as const,
      precision: "unknown" as const,
      evidenceRefs: Object.freeze([]),
    }),
  ]),
  times: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-TIME-OBSERVATION-001",
      time: Object.freeze({ stableId: "SYNTHETIC-TIME-APPROXIMATE", kind: "time" as const }),
      role: "unspecified" as const,
      precision: "approximate" as const,
      start: "1900",
      evidenceRefs: Object.freeze([]),
    }),
    Object.freeze({
      id: "SYNTHETIC-TIME-OBSERVATION-002",
      time: Object.freeze({ stableId: "SYNTHETIC-TIME-UNKNOWN", kind: "time" as const }),
      role: "unspecified" as const,
      precision: "unknown" as const,
      evidenceRefs: Object.freeze([]),
    }),
  ]),
  aggregate: Object.freeze({ visibleCount: 1, denominator: 2, unknownCount: 1, unmappedCount: 1 }),
});

export const TRACE_PUBLIC_SOURCES_FIXTURE: TraceSourcesInput = Object.freeze({
  ...base,
  sourceItems: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-SOURCE-ITEM-001",
      kind: "source_record" as const,
      ref: Object.freeze({ stableId: "SYNTHETIC-SOURCE-RECORD-001", kind: "source_record" as const }),
      evidenceRefs: Object.freeze([]),
    }),
  ]),
  sourceAssociations: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-SOURCE-ASSOCIATION-001",
      connectionKind: "source_association" as const,
      object: selectedRecord,
      sourceRecord: Object.freeze({ stableId: "SYNTHETIC-SOURCE-RECORD-001", kind: "source_record" as const }),
      associationType: "seed_description",
    }),
  ]),
  sourceLinks: Object.freeze([]),
});
