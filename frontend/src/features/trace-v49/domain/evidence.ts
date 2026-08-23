export interface TraceEvidenceRef {
  readonly stableId: string;
  readonly kind: "evidence_item" | "citation" | "locator";
  readonly locatorAvailable: boolean;
}

export interface TracePredicateDefinition {
  readonly predicateId: string;
  readonly active: boolean;
  readonly evidenceRequired: boolean;
  readonly minimumSupportCount: number;
  readonly locatorRequired?: boolean;
}

export function evidencePolicySatisfied(
  predicate: TracePredicateDefinition,
  evidenceRefs: readonly TraceEvidenceRef[],
): boolean {
  if (!predicate.active) return false;
  if (!Number.isSafeInteger(predicate.minimumSupportCount) || predicate.minimumSupportCount < 0) {
    return false;
  }
  if (!predicate.evidenceRequired) return true;
  const eligibleEvidence = predicate.locatorRequired
    ? evidenceRefs.filter((item) => item.locatorAvailable)
    : evidenceRefs;
  const uniqueSupporting = new Set(eligibleEvidence.map((item) => `${item.kind}:${item.stableId}`));
  return uniqueSupporting.size >= predicate.minimumSupportCount;
}
