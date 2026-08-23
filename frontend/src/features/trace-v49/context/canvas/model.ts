import type { TraceAccessibleRow, TracePublicDataRef } from "../../domain";
import type { TraceContextDataset } from "../types";
import {
  contextCanvasEntityId,
  type ContextCanvasDataMetadata,
  type ContextCanvasDataMode,
  type ContextCanvasGovernedContextMetadata,
  type ContextCanvasGovernedRepresentation,
} from "./types";

const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const UUID_PATTERN = /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/iu;
const VALIDATION_ID_PATTERN = /^ctxv49:/u;

const GOVERNED_KIND_CONTRACT = Object.freeze({
  medium: Object.freeze({
    explanationCode: "CTX-MEDIUM" as const,
    connectionLabel: "classified as" as const,
    sourceKind: "medium" as const,
  }),
  theme: Object.freeze({
    explanationCode: "CTX-THEME" as const,
    connectionLabel: "themed as" as const,
    sourceKind: "theme" as const,
  }),
  movement_context: Object.freeze({
    explanationCode: "CTX-MOVEMENT" as const,
    connectionLabel: "curated within" as const,
    sourceKind: "movement" as const,
  }),
});

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function requireText(value: string, field: string): void {
  if (!value.trim()) throw new Error(`Governed Context ${field} is required.`);
}

function assertPublicGovernedId(value: string, field: string): void {
  requireText(value, field);
  if (VALIDATION_ID_PATTERN.test(value) || UUID_PATTERN.test(value)) {
    throw new Error(`Governed Context ${field} is not a public governed identifier.`);
  }
}

function assertExplanation(
  representation: ContextCanvasGovernedRepresentation,
): void {
  const { explanation } = representation;
  for (const [field, value] of Object.entries({
    publicName: explanation.publicName,
    definition: explanation.definition,
    longDefinition: explanation.longDefinition,
    whyShown: explanation.whyShown,
    sourceBasis: explanation.sourceBasis,
    permittedInterpretation: explanation.permittedInterpretation,
    accessibilityWording: explanation.accessibilityWording,
  })) requireText(value, `explanation ${field}`);
  if (
    explanation.prohibitedInterpretations.length === 0
    || explanation.prohibitedInterpretations.some((value) => !value.trim())
  ) throw new Error("Governed Context prohibited interpretations are required.");
}

function assertRepresentation(
  representation: ContextCanvasGovernedRepresentation,
  policyVersion: ContextCanvasGovernedContextMetadata["policyVersion"],
): void {
  assertPublicGovernedId(representation.representationId, "representation ID");
  assertPublicGovernedId(representation.termId, "term ID");
  assertPublicGovernedId(representation.provenance.provenanceId, "provenance ID");
  requireText(representation.label, "representation label");
  requireText(representation.provenance.mappingPolicyVersion, "mapping policy version");
  const kindContract = GOVERNED_KIND_CONTRACT[representation.kind];
  if (
    representation.epistemicRole !== "project_curated_context"
    || representation.explanationCode !== kindContract.explanationCode
    || representation.connectionLabel !== kindContract.connectionLabel
    || representation.provenance.sourceKind !== kindContract.sourceKind
    || representation.provenance.basis !== "project_curated_typed_membership"
    || representation.provenance.sourceState !== "proposed"
    || representation.provenance.governancePolicyVersion !== policyVersion
  ) throw new Error(`Governed Context representation contract mismatch: ${representation.representationId}`);
  const expectedDecision = representation.publicationState === "published"
    ? "PUBLISHED"
    : "QUALIFIED";
  if (representation.provenance.decision !== expectedDecision) {
    throw new Error(`Governed Context publication decision mismatch: ${representation.representationId}`);
  }
  assertExplanation(representation);
}

export function getGovernedContextMetadata(
  dataMode: ContextCanvasDataMode,
  metadata: ContextCanvasDataMetadata,
): ContextCanvasGovernedContextMetadata | null {
  if (dataMode !== "governed_context_v1") {
    if (metadata.governedContext) {
      throw new Error("Governed Context metadata may only be used in governed_context_v1 mode.");
    }
    return null;
  }
  const governed = metadata.governedContext;
  if (!governed) throw new Error("governed_context_v1 requires governed Context metadata.");
  if (
    metadata.candidateState !== "published"
    || metadata.governedPublicRelease !== true
    || metadata.publicReleaseData !== true
    || governed.policyVersion !== "context-governance-v1"
    || !SHA256_PATTERN.test(governed.projectionSha256)
  ) throw new Error("Governed Context release metadata is inconsistent.");
  requireText(governed.projectionId, "projection ID");
  requireText(governed.explanationRegistryVersion, "explanation registry version");

  const representationIds = new Set<string>();
  const termIds = new Set<string>();
  for (const representation of governed.representations) {
    assertRepresentation(representation, governed.policyVersion);
    if (representationIds.has(representation.representationId)) {
      throw new Error(`Duplicate governed Context representation ID: ${representation.representationId}`);
    }
    if (termIds.has(representation.termId)) {
      throw new Error(`Duplicate governed Context term ID in selected dataset: ${representation.termId}`);
    }
    representationIds.add(representation.representationId);
    termIds.add(representation.termId);
  }
  return governed;
}

function uniqueRefs(values: readonly TracePublicDataRef[]): readonly TracePublicDataRef[] {
  const refs = new Map<string, TracePublicDataRef>();
  for (const value of values) {
    const id = contextCanvasEntityId(value);
    const prior = refs.get(id);
    if (prior && (prior.label !== value.label || prior.route !== value.route)) {
      throw new Error(`Conflicting Context Canvas entity identity: ${id}`);
    }
    refs.set(id, Object.freeze({ ...value }));
  }
  return Object.freeze([...refs.values()].sort((left, right) =>
    compareText(contextCanvasEntityId(left), contextCanvasEntityId(right))));
}

export function contextCanvasEntityRefsForMode(
  dataset: TraceContextDataset,
  dataMode: ContextCanvasDataMode,
  metadata: ContextCanvasDataMetadata,
): readonly TracePublicDataRef[] {
  if (dataMode === "synthetic_contract") return uniqueRefs(dataset.items);
  if (dataMode === "real_v49_validation") {
    return uniqueRefs([
      dataset.selectedRecord,
      ...dataset.controlledAssignments.flatMap((assignment) => [assignment.subject, assignment.value]),
    ]);
  }
  const governed = getGovernedContextMetadata(dataMode, metadata);
  if (!governed) throw new Error("Governed Context metadata is unavailable.");
  return uniqueRefs([
    dataset.selectedRecord,
    ...governed.representations.map((representation) => Object.freeze({
      stableId: representation.termId,
      kind: "controlled_term" as const,
      label: representation.label,
    })),
  ]);
}

export function contextCanvasRepresentationByEntityId(
  dataMode: ContextCanvasDataMode,
  metadata: ContextCanvasDataMetadata,
): ReadonlyMap<string, ContextCanvasGovernedRepresentation> {
  const governed = getGovernedContextMetadata(dataMode, metadata);
  if (!governed) return new Map();
  return new Map(governed.representations.map((representation) => [
    contextCanvasEntityId({ stableId: representation.termId, kind: "controlled_term" }),
    representation,
  ]));
}

export function contextCanvasAccessibleRowsForMode(
  dataset: TraceContextDataset,
  dataMode: ContextCanvasDataMode,
  metadata: ContextCanvasDataMetadata,
): readonly TraceAccessibleRow[] {
  if (dataMode === "synthetic_contract") return dataset.accessibleRows;
  if (dataMode === "real_v49_validation") {
    const allowedRowIds = new Set([
      `selected:${dataset.selectedRecord.stableId}`,
      ...dataset.controlledAssignments.map((assignment) => `assignment:${assignment.id}`),
    ]);
    return Object.freeze(dataset.accessibleRows.filter((row) => allowedRowIds.has(row.id)));
  }
  const governed = getGovernedContextMetadata(dataMode, metadata);
  if (!governed) throw new Error("Governed Context metadata is unavailable.");
  const rootValues: Array<Readonly<{ label: string; value: string }>> = [
    Object.freeze({ label: "Stable public ID", value: dataset.selectedRecord.stableId }),
  ];
  const rootMetadata = governed.rootMetadata;
  if (rootMetadata) {
    const fields = [
      ["Source-reported attribution", rootMetadata.creatorAttribution],
      ["Source-reported object type", rootMetadata.objectType],
      ["Source-reported date", rootMetadata.dateDisplay],
      ["Source name", rootMetadata.sourceName],
    ] as const;
    for (const [label, value] of fields) {
      if (value.trim()) rootValues.push(Object.freeze({ label, value }));
    }
  }
  return Object.freeze([
    Object.freeze({
      id: `selected:${dataset.selectedRecord.stableId}`,
      category: "selected_record",
      label: dataset.selectedRecord.label?.trim() || dataset.selectedRecord.stableId,
      values: Object.freeze(rootValues),
    }),
    ...governed.representations.map((representation) => Object.freeze({
      id: `representation:${representation.representationId}`,
      category: "context_representation",
      label: `${dataset.selectedRecord.label?.trim() || dataset.selectedRecord.stableId} — ${representation.connectionLabel} — ${representation.label}`,
      values: Object.freeze([
        Object.freeze({ label: "Context type", value: representation.explanation.publicName }),
        Object.freeze({ label: "Full label", value: representation.label }),
        Object.freeze({ label: "Meaning", value: representation.explanation.longDefinition }),
        Object.freeze({ label: "Why shown", value: representation.explanation.whyShown }),
        Object.freeze({ label: "Epistemic role", value: representation.epistemicRole }),
        Object.freeze({ label: "Publication state", value: representation.publicationState }),
        Object.freeze({ label: "Source basis", value: representation.explanation.sourceBasis }),
        Object.freeze({ label: "Source state", value: representation.provenance.sourceState }),
        Object.freeze({ label: "Governance decision", value: representation.provenance.decision }),
        Object.freeze({ label: "Permitted interpretation", value: representation.explanation.permittedInterpretation }),
        Object.freeze({
          label: "Prohibited interpretations",
          value: representation.explanation.prohibitedInterpretations.join("; "),
        }),
        Object.freeze({ label: "Explanation code", value: representation.explanationCode }),
        Object.freeze({ label: "Public provenance ID", value: representation.provenance.provenanceId }),
        Object.freeze({ label: "Mapping policy version", value: representation.provenance.mappingPolicyVersion }),
        Object.freeze({ label: "Governance policy version", value: representation.provenance.governancePolicyVersion }),
      ]),
    })),
  ]);
}

export function contextCanvasSessionKey(
  dataset: TraceContextDataset,
  dataMode: ContextCanvasDataMode,
  metadata: ContextCanvasDataMetadata,
): string {
  const governed = getGovernedContextMetadata(dataMode, metadata);
  return JSON.stringify([
    dataMode,
    dataset.release.manifestSha256,
    governed?.projectionId ?? null,
    governed?.projectionSha256 ?? null,
    dataset.selectedRecord.stableId,
  ]);
}
