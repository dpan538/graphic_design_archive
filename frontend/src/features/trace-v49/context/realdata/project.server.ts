import "server-only";

import { createHash } from "node:crypto";
import { deriveContextTraceDataset } from "../project";
import type { TraceControlledAssignment, TraceCuratedMembership, TracePublicDataRef } from "../../domain";
import {
  TRACE_CONTEXT_REALDATA_MAPPING_VERSION,
  type TraceContextValidationFolderCandidate,
  type TraceContextValidationFolderType,
  type TraceContextValidationProjection,
  type TraceContextValidationRecordCandidate,
} from "./types";

export const TRACE_CONTEXT_REALDATA_RELEASE_ID = "trace-v49-context-validation-round2-v1" as const;
export const TRACE_CONTEXT_REALDATA_FROZEN_INPUT_SHA256 = Object.freeze({
  "data/prefreeze_candidate_v48.sqlite": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
  "database/FREEZE_V49.json": "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e",
  "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv": "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01",
} as const);
export const TRACE_CONTEXT_REALDATA_MANIFEST_SHA256 = createHash("sha256")
  .update([
    `mapping:${TRACE_CONTEXT_REALDATA_MAPPING_VERSION}`,
    ...Object.entries(TRACE_CONTEXT_REALDATA_FROZEN_INPUT_SHA256)
      .sort(([left], [right]) => compareText(left, right))
      .map(([path, sha256]) => `${path}:${sha256}`),
  ].join("\n"), "utf8")
  .digest("hex");

const CONTROLLED_FOLDER_TYPES = new Set<TraceContextValidationFolderType>([
  "medium",
  "theme",
  "movement",
]);
const INVALID_XML_CONTROL = /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function validationHash(namespace: string, parts: readonly string[]): string {
  return createHash("sha256")
    .update([TRACE_CONTEXT_REALDATA_MAPPING_VERSION, namespace, ...parts].join("\u0000"), "utf8")
    .digest("hex");
}

function validationId(namespace: string, parts: readonly string[]): string {
  return `ctxv49:${namespace}:${validationHash(namespace, parts)}`;
}

function assertSourceIdentity(value: string, field: string): void {
  if (!value.trim()) throw new Error(`${field} is required`);
  if (INVALID_XML_CONTROL.test(value)) throw new Error(`${field} contains an invalid control character`);
}

function assertCanonicalLabel(value: string, field: string): void {
  if (!value.trim()) throw new Error(`${field} is empty`);
  if (INVALID_XML_CONTROL.test(value)) throw new Error(`${field} contains an invalid control character`);
}

function compareFolderCandidate(
  left: TraceContextValidationFolderCandidate,
  right: TraceContextValidationFolderCandidate,
): number {
  return compareText(left.folderType, right.folderType)
    || compareText(left.folderToken, right.folderToken);
}

export function projectRealContextValidationDataset(
  candidate: TraceContextValidationRecordCandidate,
): TraceContextValidationProjection {
  assertSourceIdentity(candidate.stableId, "selected public stable ID");
  if (UUID_PATTERN.test(candidate.stableId)) {
    throw new Error("selected public stable ID contains an internal UUID");
  }
  assertCanonicalLabel(candidate.title, "selected public title");

  const selectedRecord: TracePublicDataRef = Object.freeze({
    stableId: candidate.stableId,
    kind: "archive_object" as const,
    label: candidate.title,
  });
  const controlledAssignments: TraceControlledAssignment[] = [];
  const curatedMemberships: TraceCuratedMembership[] = [];
  const sourceIdentityFingerprints = new Map<string, string>();

  for (const folder of [...candidate.folders].sort(compareFolderCandidate)) {
    assertSourceIdentity(folder.folderToken, `${folder.folderType} folder token`);
    assertCanonicalLabel(folder.label, `${folder.folderType} folder label`);
    const sourceKey = `${folder.folderType}\u0000${folder.folderToken}`;
    const priorLabel = sourceIdentityFingerprints.get(sourceKey);
    if (priorLabel !== undefined && priorLabel !== folder.label) {
      throw new Error(`conflicting validation source identity: ${sourceKey}`);
    }
    if (priorLabel !== undefined) continue;
    sourceIdentityFingerprints.set(sourceKey, folder.label);

    if (CONTROLLED_FOLDER_TYPES.has(folder.folderType)) {
      const value = Object.freeze({
        stableId: validationId(folder.folderType, [folder.folderToken]),
        kind: "controlled_term" as const,
        label: folder.label,
      });
      controlledAssignments.push(Object.freeze({
        id: validationId("assignment", [candidate.stableId, folder.folderType, folder.folderToken]),
        connectionKind: "controlled_assignment" as const,
        subject: selectedRecord,
        value,
        assignmentType: `validation_${folder.folderType}_candidate`,
        state: "proposed" as const,
      }));
    }

    const container = Object.freeze({
      stableId: validationId("folder", [folder.folderType, folder.folderToken]),
      kind: "controlled_term" as const,
      label: folder.label,
    });
    curatedMemberships.push(Object.freeze({
      id: validationId("membership", [candidate.stableId, folder.folderType, folder.folderToken]),
      connectionKind: "curated_membership" as const,
      member: selectedRecord,
      container,
      membershipType: `validation_folder_membership:${folder.folderType}`,
      state: "proposed" as const,
    }));
  }

  const dataset = deriveContextTraceDataset({
    release: Object.freeze({
      releaseId: TRACE_CONTEXT_REALDATA_RELEASE_ID,
      manifestSha256: TRACE_CONTEXT_REALDATA_MANIFEST_SHA256,
    }),
    publicObjectStableIds: Object.freeze([candidate.stableId]),
    availability: Object.freeze({
      state: "not_published" as const,
      reasonCodes: Object.freeze([
        "NO_GOVERNED_PUBLIC_CONTEXT_RELEASE",
        "UNREVIEWED_VALIDATION_CANDIDATES",
        "VALIDATION_ONLY",
      ]),
      message: "Real v49 Context candidates are available only in a local validation mode and are not published.",
    }),
    selectedRecord,
    predicateRegistry: Object.freeze([]),
    semanticEdges: Object.freeze([]),
    unknowns: Object.freeze([]),
    warnings: Object.freeze([
      "All controlled assignments and curated memberships are validation-only proposed candidates.",
      "No accepted v49 semantic relations exist.",
    ]),
    denominator: candidate.folders.length,
    controlledAssignments: Object.freeze(controlledAssignments),
    curatedMemberships: Object.freeze(curatedMemberships),
  });

  return Object.freeze({
    dataset,
    metadata: Object.freeze({
      dataMode: "real_v49_validation" as const,
      mappingVersion: TRACE_CONTEXT_REALDATA_MAPPING_VERSION,
      sourceReleaseTag: "v49-data-api-closure-20260821" as const,
      selectedPublicStableId: candidate.stableId,
      candidateState: "not_published" as const,
      governedPublicRelease: false as const,
      historicalEvidence: false as const,
      publicReleaseData: false as const,
    }),
  });
}
