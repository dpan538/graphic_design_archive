import type { TraceContextInput } from "../types";
import { deriveContextTraceDataset } from "../project";

export const CONTEXT_CANVAS_FIXTURE_METADATA = Object.freeze({
  fixtureKind: "synthetic-contract-only" as const,
  historicalEvidence: false as const,
  publicReleaseData: false as const,
});

const objectA = Object.freeze({
  stableId: "SYNTHETIC-PUBLIC-OBJECT-A",
  kind: "archive_object" as const,
  label: "Object A",
});

const objectJ = Object.freeze({
  stableId: "SYNTHETIC-PUBLIC-OBJECT-J",
  kind: "archive_object" as const,
  label: "Object J",
});

const mediumB = Object.freeze({
  stableId: "SYNTHETIC-CONTROLLED-MEDIUM-B",
  kind: "controlled_term" as const,
  label: "Medium B",
});

const themeC = Object.freeze({
  stableId: "SYNTHETIC-CONTROLLED-THEME-C",
  kind: "controlled_term" as const,
  label: "Theme C",
});

const typeE = Object.freeze({
  stableId: "SYNTHETIC-CONTROLLED-TYPE-E",
  kind: "controlled_term" as const,
  label: "Type E",
});

const collectionF = Object.freeze({
  stableId: "SYNTHETIC-CONTROLLED-COLLECTION-F",
  kind: "controlled_term" as const,
  label: "Collection F",
});

const pathwayD = Object.freeze({
  stableId: "SYNTHETIC-CURATED-PATHWAY-D",
  kind: "controlled_term" as const,
  label: "Pathway D",
});

const pathwayG = Object.freeze({
  stableId: "SYNTHETIC-CURATED-PATHWAY-G",
  kind: "controlled_term" as const,
  label: "Pathway G",
});

const pathwayH = Object.freeze({
  stableId: "SYNTHETIC-CURATED-PATHWAY-H",
  kind: "controlled_term" as const,
  label: "Pathway H",
});

const pathwayI = Object.freeze({
  stableId: "SYNTHETIC-CURATED-PATHWAY-I",
  kind: "controlled_term" as const,
  label: "Pathway I",
});

export const CONTEXT_CANVAS_SYNTHETIC_INPUT: TraceContextInput = Object.freeze({
  release: Object.freeze({
    releaseId: "v49-context-canvas-synthetic-contract",
    manifestSha256: "4949494949494949494949494949494949494949494949494949494949494949",
  }),
  publicObjectStableIds: Object.freeze([objectA.stableId, objectJ.stableId]),
  availability: Object.freeze({
    state: "not_published" as const,
    reasonCodes: Object.freeze(["SYNTHETIC_CONTRACT_ONLY"]),
    message: "Synthetic functional contract fixture; not a governed public projection.",
  }),
  selectedRecord: objectA,
  predicateRegistry: Object.freeze([
    Object.freeze({
      predicateId: "synthetic_contextual_companion",
      active: true,
      evidenceRequired: true,
      minimumSupportCount: 1,
      locatorRequired: true,
    }),
  ]),
  semanticEdges: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-SEMANTIC-EDGE-001",
      semantic: true as const,
      status: "accepted" as const,
      predicateId: "synthetic_contextual_companion",
      subject: objectA,
      object: objectJ,
      evidenceRefs: Object.freeze([
        Object.freeze({
          stableId: "SYNTHETIC-EVIDENCE-LOCATOR-001",
          kind: "locator" as const,
          locatorAvailable: true,
        }),
      ]),
    }),
  ]),
  controlledAssignments: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-ASSIGNMENT-001",
      connectionKind: "controlled_assignment" as const,
      subject: objectA,
      value: mediumB,
      assignmentType: "medium",
      state: "proposed" as const,
    }),
    Object.freeze({
      id: "SYNTHETIC-ASSIGNMENT-002",
      connectionKind: "controlled_assignment" as const,
      subject: objectA,
      value: themeC,
      assignmentType: "theme",
      state: "proposed" as const,
    }),
    Object.freeze({
      id: "SYNTHETIC-ASSIGNMENT-003",
      connectionKind: "controlled_assignment" as const,
      subject: objectA,
      value: typeE,
      assignmentType: "object_type",
      state: "proposed" as const,
    }),
    Object.freeze({
      id: "SYNTHETIC-ASSIGNMENT-004",
      connectionKind: "controlled_assignment" as const,
      subject: objectA,
      value: collectionF,
      assignmentType: "collection",
      state: "proposed" as const,
    }),
  ]),
  curatedMemberships: Object.freeze([
    Object.freeze({
      id: "SYNTHETIC-MEMBERSHIP-001",
      connectionKind: "curated_membership" as const,
      member: objectA,
      container: pathwayD,
      membershipType: "research_pathway",
      state: "proposed" as const,
    }),
    Object.freeze({
      id: "SYNTHETIC-MEMBERSHIP-002",
      connectionKind: "curated_membership" as const,
      member: objectA,
      container: pathwayG,
      membershipType: "research_pathway",
      state: "proposed" as const,
    }),
    Object.freeze({
      id: "SYNTHETIC-MEMBERSHIP-003",
      connectionKind: "curated_membership" as const,
      member: objectA,
      container: pathwayH,
      membershipType: "folder_membership",
      state: "proposed" as const,
    }),
    Object.freeze({
      id: "SYNTHETIC-MEMBERSHIP-004",
      connectionKind: "curated_membership" as const,
      member: objectA,
      container: pathwayI,
      membershipType: "folder_membership",
      state: "proposed" as const,
    }),
  ]),
  unknowns: Object.freeze([]),
  warnings: Object.freeze([
    "SYNTHETIC_CONTRACT_ONLY",
    "SYNTHETIC_SEMANTIC_EDGE_NOT_HISTORICAL_EVIDENCE",
  ]),
  denominator: 2,
});

export const CONTEXT_CANVAS_SYNTHETIC_DATASET = deriveContextTraceDataset(
  CONTEXT_CANVAS_SYNTHETIC_INPUT,
);
