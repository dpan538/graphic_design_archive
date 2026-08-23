import type {
  PublicSpacetimeAtlasDataset,
  PublicSpacetimeRecordPage,
  PublicSpacetimeRecordSummary,
} from "../governed/types";

export type SpacetimeRequestChannel = "atlas" | "records";

export interface SpacetimeRequestTicket {
  readonly channel: SpacetimeRequestChannel;
  readonly epoch: number;
  readonly signal: AbortSignal;
  isCurrent(): boolean;
}

export interface SpacetimeAtlasRequestIdentity {
  readonly spacetimeProjectionSha256: string;
  readonly periodId: string;
}

export interface SpacetimeRecordDatasetIdentity extends SpacetimeAtlasRequestIdentity {
  readonly geographyId: string;
}

export interface SpacetimeRecordPageRequestIdentity extends SpacetimeRecordDatasetIdentity {
  readonly after: string | null;
}

export interface SpacetimeRecordAccumulator {
  readonly identity: SpacetimeRecordDatasetIdentity;
  readonly page: PublicSpacetimeRecordPage;
  readonly records: readonly PublicSpacetimeRecordSummary[];
}

export class SpacetimeRequestEpochGate {
  private readonly epochs: Record<SpacetimeRequestChannel, number> = {
    atlas: 0,
    records: 0,
  };
  private readonly controllers: Partial<Record<SpacetimeRequestChannel, AbortController>> = {};

  begin(channel: SpacetimeRequestChannel): SpacetimeRequestTicket {
    this.controllers[channel]?.abort();
    const controller = new AbortController();
    const epoch = this.epochs[channel] + 1;
    this.epochs[channel] = epoch;
    this.controllers[channel] = controller;
    return Object.freeze({
      channel,
      epoch,
      signal: controller.signal,
      isCurrent: () =>
        !controller.signal.aborted
        && this.epochs[channel] === epoch
        && this.controllers[channel] === controller,
    });
  }

  abort(channel: SpacetimeRequestChannel): void {
    this.controllers[channel]?.abort();
    delete this.controllers[channel];
    this.epochs[channel] += 1;
  }

  abortAll(): void {
    this.abort("atlas");
    this.abort("records");
  }

  /** Test-only snapshot; it contains no request data. */
  diagnosticsForTests(): Readonly<Record<SpacetimeRequestChannel, number>> {
    return Object.freeze({ ...this.epochs });
  }
}

export function spacetimeAtlasResultMatches(
  identity: SpacetimeAtlasRequestIdentity,
  atlas: PublicSpacetimeAtlasDataset,
): boolean {
  return atlas.release.spacetimeProjectionSha256 === identity.spacetimeProjectionSha256
    && atlas.selectedPeriod.periodId === identity.periodId;
}

export function spacetimeRecordPageMatches(
  identity: SpacetimeRecordDatasetIdentity,
  page: PublicSpacetimeRecordPage,
): boolean {
  return page.release.spacetimeProjectionSha256 === identity.spacetimeProjectionSha256
    && page.period.periodId === identity.periodId
    && page.geography.geographyId === identity.geographyId;
}

export function applySpacetimeRecordPage(
  current: SpacetimeRecordAccumulator | null,
  request: SpacetimeRecordPageRequestIdentity,
  page: PublicSpacetimeRecordPage,
): SpacetimeRecordAccumulator {
  if (!spacetimeRecordPageMatches(request, page)) {
    throw new Error("Spacetime record response identity differs from its request");
  }
  const identity = Object.freeze({
    spacetimeProjectionSha256: request.spacetimeProjectionSha256,
    periodId: request.periodId,
    geographyId: request.geographyId,
  });
  if (page.nodes.length > page.totalCount) {
    throw new Error("Spacetime record page exceeds its governed total");
  }
  if (new Set(page.nodes.map((record) => record.stableId)).size !== page.nodes.length) {
    throw new Error("Spacetime record page repeats a public record");
  }
  if (request.after === null) {
    return Object.freeze({
      identity,
      page,
      records: Object.freeze([...page.nodes]),
    });
  }
  if (
    !current
    || current.identity.spacetimeProjectionSha256 !== request.spacetimeProjectionSha256
    || current.identity.periodId !== request.periodId
    || current.identity.geographyId !== request.geographyId
    || !spacetimeRecordPageMatches(request, current.page)
  ) {
    throw new Error("stale Spacetime cursor cannot append to another dataset");
  }
  if (current.page.pageInfo.endCursor !== request.after) {
    throw new Error("stale Spacetime cursor cannot append after another page");
  }
  if (current.page.totalCount !== page.totalCount) {
    throw new Error("Spacetime record page total changed during pagination");
  }
  const seen = new Set(current.records.map((record) => record.stableId));
  if (page.nodes.some((record) => seen.has(record.stableId))) {
    throw new Error("Spacetime record page repeats an existing public record");
  }
  const records = Object.freeze([...current.records, ...page.nodes]);
  if (records.length > page.totalCount) {
    throw new Error("Spacetime record pages exceed their governed total");
  }
  return Object.freeze({ identity, page, records });
}
