export interface TraceReleaseRef {
  readonly releaseId: string;
  readonly manifestSha256: string;
}

export function assertTraceReleaseRef(value: TraceReleaseRef): void {
  if (!value.releaseId.trim()) throw new Error("TRACE releaseId is required");
  if (!/^[0-9a-f]{64}$/.test(value.manifestSha256)) {
    throw new Error("TRACE manifestSha256 must be a lowercase SHA-256");
  }
}
