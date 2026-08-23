import { deriveContextTraceDataset } from "../project";
import type { TraceContextDataset } from "../types";
import type {
  ContextCanvasDataMetadata,
  ContextCanvasGovernedRepresentation,
} from "../canvas/types";
import {
  TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION,
  TRACE_CONTEXT_GOVERNED_MAPPING_VERSION,
  type PublicContextDataset,
  type PublicContextExplanation,
  type PublicContextRepresentation,
} from "./types";

export const TRACE_CONTEXT_PUBLIC_OBJECT_COUNT = 7_995 as const;

export interface GovernedContextCanvasInput {
  readonly dataset: TraceContextDataset;
  readonly dataMode: "governed_context_v1";
  readonly metadata: ContextCanvasDataMetadata;
}

const GOVERNED_KIND_CONTRACT = Object.freeze({
  medium: Object.freeze({
    explanationCode: "CTX-MEDIUM" as const,
    connectionLabel: "classified as" as const,
  }),
  theme: Object.freeze({
    explanationCode: "CTX-THEME" as const,
    connectionLabel: "themed as" as const,
  }),
  movement_context: Object.freeze({
    explanationCode: "CTX-MOVEMENT" as const,
    connectionLabel: "curated within" as const,
  }),
});

function substituteTerm(value: string, label: string): string {
  return value.replaceAll("{term}", label);
}

function explanationForRepresentation(
  representation: PublicContextRepresentation,
  explanations: ReadonlyMap<string, PublicContextExplanation>,
): PublicContextExplanation {
  const explanation = explanations.get(representation.explanationCode);
  if (!explanation || explanation.contextKind !== representation.kind) {
    throw new Error(`Governed Context explanation did not resolve: ${representation.id}`);
  }
  return explanation;
}

function toCanvasRepresentation(
  representation: PublicContextRepresentation,
  explanations: ReadonlyMap<string, PublicContextExplanation>,
): ContextCanvasGovernedRepresentation {
  const contract = GOVERNED_KIND_CONTRACT[representation.kind];
  const explanation = explanationForRepresentation(representation, explanations);
  if (
    representation.explanationCode !== contract.explanationCode
    || explanation.connectionLabel !== contract.connectionLabel
  ) {
    throw new Error(`Governed Context kind contract did not resolve: ${representation.id}`);
  }
  return Object.freeze({
    representationId: representation.id,
    termId: representation.termId,
    kind: representation.kind,
    label: representation.label,
    epistemicRole: representation.epistemicRole,
    publicationState: representation.publicationState,
    explanationCode: contract.explanationCode,
    connectionLabel: contract.connectionLabel,
    explanation: Object.freeze({
      publicName: explanation.publicLabel,
      definition: explanation.shortDefinition,
      longDefinition: explanation.longDefinition,
      whyShown: substituteTerm(explanation.uiShortExplanation, representation.label),
      sourceBasis: explanation.sourceBasis,
      permittedInterpretation: substituteTerm(
        explanation.permittedInterpretation,
        representation.label,
      ),
      prohibitedInterpretations: Object.freeze([...explanation.prohibitedInterpretations]),
      accessibilityWording: substituteTerm(
        explanation.accessibilityWording,
        representation.label,
      ),
    }),
    provenance: Object.freeze({ ...representation.provenance }),
  });
}

export function adaptPublicContextDatasetForCanvas(
  publicDataset: PublicContextDataset,
): GovernedContextCanvasInput {
  const root = Object.freeze({
    stableId: publicDataset.selectedRecord.surfaceId,
    kind: "archive_object" as const,
    label: publicDataset.selectedRecord.title,
  });
  const explanations = new Map(
    publicDataset.explanations.map((explanation) => [explanation.explanationCode, explanation]),
  );
  if (explanations.size !== publicDataset.explanations.length) {
    throw new Error("Governed Context explanation codes must be unique.");
  }
  const governedRepresentations = Object.freeze(
    publicDataset.representations.map((representation) =>
      toCanvasRepresentation(representation, explanations)),
  );
  const termRefs = new Map<string, Readonly<{
    stableId: string;
    kind: "controlled_term";
    label: string;
  }>>();
  for (const representation of publicDataset.representations) {
    const prior = termRefs.get(representation.termId);
    if (prior && prior.label !== representation.label) {
      throw new Error(`Governed Context term identity has conflicting labels: ${representation.termId}`);
    }
    termRefs.set(representation.termId, Object.freeze({
      stableId: representation.termId,
      kind: "controlled_term" as const,
      label: representation.label,
    }));
  }
  const controlledAssignments = Object.freeze(publicDataset.representations.map(
    (representation) => Object.freeze({
      id: representation.id,
      connectionKind: "controlled_assignment" as const,
      subject: root,
      value: termRefs.get(representation.termId)!,
      assignmentType: representation.kind,
      state: "proposed" as const,
    }),
  ));
  const dataset = deriveContextTraceDataset(Object.freeze({
    release: Object.freeze({
      releaseId: publicDataset.release.researchReleaseId,
      manifestSha256: publicDataset.release.researchManifestSha256,
    }),
    publicObjectStableIds: Object.freeze([root.stableId]),
    availability: Object.freeze({
      state: publicDataset.availability === "ready" ? "ready" as const : "empty" as const,
      reasonCodes: Object.freeze(publicDataset.availability === "ready"
        ? []
        : ["NO_GOVERNED_CONTEXT_REPRESENTATIONS"]),
      message: publicDataset.availability === "ready"
        ? "Governed project-curated Context representations are available."
        : "No governed Context representations are available for this public record.",
    }),
    selectedRecord: root,
    predicateRegistry: Object.freeze([]),
    semanticEdges: Object.freeze([]),
    controlledAssignments,
    curatedMemberships: Object.freeze([]),
    unknowns: Object.freeze([]),
    warnings: Object.freeze([
      "PROJECT_CURATED_CONTEXT_NOT_A_HISTORICAL_RELATION",
      "CURATED_MEMBERSHIP_IS_PROVENANCE_ONLY",
      "REGION_IS_DEFERRED_TO_SPACETIME",
    ]),
    denominator: 1,
  }));
  const metadata: ContextCanvasDataMetadata = Object.freeze({
    dataLabel: "governed Context V1",
    mappingVersion: publicDataset.representations[0]?.provenance.mappingPolicyVersion
      ?? TRACE_CONTEXT_GOVERNED_MAPPING_VERSION,
    candidateState: "published" as const,
    historicalEvidence: false as const,
    governedPublicRelease: true,
    publicReleaseData: true,
    publicObjectCohortCount: TRACE_CONTEXT_PUBLIC_OBJECT_COUNT,
    governedContext: Object.freeze({
      projectionId: publicDataset.release.contextProjectionId,
      projectionSha256: publicDataset.release.contextProjectionSha256,
      policyVersion: TRACE_CONTEXT_GOVERNANCE_POLICY_VERSION,
      explanationRegistryVersion: publicDataset.explanationRegistryVersion,
      rootMetadata: Object.freeze({ ...publicDataset.selectedRecord.rootMetadata }),
      representations: governedRepresentations,
    }),
  });
  return Object.freeze({
    dataset,
    dataMode: "governed_context_v1" as const,
    metadata,
  });
}
