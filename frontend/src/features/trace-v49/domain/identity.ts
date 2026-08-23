export type TracePublicDataKind =
  | "archive_object"
  | "controlled_term"
  | "place"
  | "time"
  | "source"
  | "source_record"
  | "evidence_item"
  | "claim"
  | "relation";

export type TraceDomain = "context" | "spacetime" | "sources";

export interface TracePublicDataRef {
  readonly stableId: string;
  readonly kind: TracePublicDataKind;
  readonly label?: string;
  readonly route?: string;
}

export function compareTraceIdentity(left: TracePublicDataRef, right: TracePublicDataRef): number {
  return left.kind < right.kind ? -1 : left.kind > right.kind ? 1
    : left.stableId < right.stableId ? -1 : left.stableId > right.stableId ? 1 : 0;
}

export function assertPublicArchiveRefs(
  refs: readonly TracePublicDataRef[],
  publicObjectStableIds: ReadonlySet<string>,
): void {
  for (const ref of refs) {
    if (!ref.stableId.trim()) throw new Error("TRACE public reference stableId is required");
    if (ref.kind === "archive_object" && !publicObjectStableIds.has(ref.stableId)) {
      throw new Error(`non-public archive object in TRACE projection: ${ref.stableId}`);
    }
  }
}
