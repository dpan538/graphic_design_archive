import type { TraceEvidenceRef, TracePredicateDefinition } from "./evidence";
import type { TracePublicDataRef } from "./identity";
import { evidencePolicySatisfied } from "./evidence";

export interface TraceSemanticEdge {
  readonly id: string;
  readonly semantic: true;
  readonly status: "accepted";
  readonly predicateId: string;
  readonly subject: TracePublicDataRef;
  readonly object: TracePublicDataRef;
  readonly evidenceRefs: readonly TraceEvidenceRef[];
}

export interface TraceVisualGuide {
  readonly id: string;
  readonly kind: string;
  readonly semantic: false;
}

export interface TraceControlledAssignment {
  readonly id: string;
  readonly connectionKind: "controlled_assignment";
  readonly subject: TracePublicDataRef;
  readonly value: TracePublicDataRef;
  readonly assignmentType: string;
  readonly state: "accepted" | "proposed";
}

export interface TraceCuratedMembership {
  readonly id: string;
  readonly connectionKind: "curated_membership";
  readonly member: TracePublicDataRef;
  readonly container: TracePublicDataRef;
  readonly membershipType: string;
  readonly state: "accepted" | "proposed";
}

export interface TraceSourceAssociation {
  readonly id: string;
  readonly connectionKind: "source_association";
  readonly object: TracePublicDataRef;
  readonly sourceRecord: TracePublicDataRef;
  readonly associationType: string;
}

export type TraceConnection =
  | TraceSemanticEdge
  | TraceControlledAssignment
  | TraceCuratedMembership
  | TraceSourceAssociation;

export function assertAcceptedSemanticEdge(
  edge: TraceSemanticEdge,
  predicates: ReadonlyMap<string, TracePredicateDefinition>,
): void {
  const predicate = predicates.get(edge.predicateId);
  if (!predicate) throw new Error(`unregistered TRACE predicate: ${edge.predicateId}`);
  if (!evidencePolicySatisfied(predicate, edge.evidenceRefs)) {
    throw new Error(`TRACE evidence policy not satisfied: ${edge.id}`);
  }
}
