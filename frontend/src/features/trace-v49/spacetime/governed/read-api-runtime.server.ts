import "server-only";

import type { ArchiveVersionRef, RepoResult, RepositoryErrorCode } from "@/lib/read-platform/types";
import type {
  PublicSpacetimeAtlasDataset,
  PublicSpacetimePeriodsDataset,
  PublicSpacetimeRecordPage,
} from "./types";
import {
  getGovernedSpacetimePeriodsDataset,
  getGovernedSpacetimeProjectionInfo,
  lookupGovernedSpacetimeAtlas,
  lookupGovernedSpacetimeGeographyRecords,
} from "./reader.server";

type GovernedSpacetimeApiData =
  | PublicSpacetimePeriodsDataset
  | PublicSpacetimeAtlasDataset
  | PublicSpacetimeRecordPage;

export type GovernedSpacetimeReadApiMatch =
  | Readonly<{ matched: false }>
  | Readonly<{
    matched: true;
    result: RepoResult<GovernedSpacetimeApiData>;
    version?: ArchiveVersionRef;
  }>;

const PERIODS_PATH_LENGTH = 5;
const GEOGRAPHY_RECORDS_PATH_LENGTH = 7;
const MAX_PAGE_SIZE = 100;
const MAX_CURSOR_LENGTH = 2_048;

function resourceKind(
  path: readonly string[],
): "periods" | "atlas" | "geography-records" | null {
  if (
    path.length === PERIODS_PATH_LENGTH
    && path[0] === "releases"
    && Boolean(path[1])
    && path[2] === "trace"
    && path[3] === "spacetime"
  ) {
    if (path[4] === "periods") return "periods";
    if (path[4] === "atlas") return "atlas";
  }
  if (
    path.length === GEOGRAPHY_RECORDS_PATH_LENGTH
    && path[0] === "releases"
    && Boolean(path[1])
    && path[2] === "trace"
    && path[3] === "spacetime"
    && path[4] === "geographies"
    && Boolean(path[5])
    && path[6] === "records"
  ) return "geography-records";
  return null;
}

function versionFor(
  researchReleaseId: string,
  researchManifestSha256: string,
): ArchiveVersionRef {
  return Object.freeze({
    research: Object.freeze({
      apiVersion: "v1" as const,
      researchReleaseId,
      researchManifestSha256,
      schemaVersion: "archive-research-release/v1" as const,
    }),
    visual: null,
    visualState: "UNAVAILABLE" as const,
    visualReasonCodes: Object.freeze([
      "VISUAL_REGISTRY_UNAVAILABLE",
      "POSITIVE_VISUAL_RIGHTS_COUNT_ZERO",
    ]),
    takedownOverlaySha256: null,
  });
}

function failure(
  code: RepositoryErrorCode,
  message: string,
): RepoResult<GovernedSpacetimeApiData> {
  return Object.freeze({
    ok: false as const,
    error: Object.freeze({ code, message, retryable: false }),
  });
}

function matchedFailure(
  code: RepositoryErrorCode,
  message: string,
  version?: ArchiveVersionRef,
): GovernedSpacetimeReadApiMatch {
  return Object.freeze({
    matched: true as const,
    result: failure(code, message),
    ...(version ? { version } : {}),
  });
}

function allowedQueryOnly(
  searchParams: URLSearchParams,
  allowed: ReadonlySet<string>,
): boolean {
  return [...searchParams.keys()].every((key) => allowed.has(key));
}

function exactlyOne(
  searchParams: URLSearchParams,
  name: string,
): string | null {
  const values = searchParams.getAll(name);
  if (values.length !== 1 || values[0].length === 0) return null;
  return values[0];
}

function optionalOnce(
  searchParams: URLSearchParams,
  name: string,
): string | undefined | null {
  const values = searchParams.getAll(name);
  if (values.length === 0) return undefined;
  if (values.length !== 1 || values[0].length === 0) return null;
  return values[0];
}

/**
 * Resolve the three governed Spacetime resources without opening the generic
 * archive repository. The controller calls this only for an exact resource
 * shape, before Search or database-backed providers can enter the import graph.
 */
export function tryReadGovernedSpacetimeApiResource(
  path: readonly string[],
  searchParams: URLSearchParams,
  requestedManifestSha256: string | null,
): GovernedSpacetimeReadApiMatch {
  const kind = resourceKind(path);
  if (!kind) return Object.freeze({ matched: false as const });

  let info: ReturnType<typeof getGovernedSpacetimeProjectionInfo>;
  try {
    info = getGovernedSpacetimeProjectionInfo();
  } catch {
    return matchedFailure(
      "INTEGRITY_FAILURE",
      "the governed Spacetime projection failed validation",
    );
  }

  const requestedReleaseId = path[1];
  if (
    requestedReleaseId !== "current"
    && (
      requestedReleaseId !== info.researchReleaseId
      || requestedManifestSha256 !== info.researchManifestSha256
    )
  ) {
    return matchedFailure(
      "RELEASE_NOT_FOUND",
      "requested exact research release pair is unavailable",
    );
  }

  const version = versionFor(info.researchReleaseId, info.researchManifestSha256);
  if (kind === "periods") {
    if (!allowedQueryOnly(searchParams, new Set())) {
      return matchedFailure(
        "INVALID_ARGUMENT",
        "the Spacetime periods resource does not accept query parameters",
        version,
      );
    }
    try {
      return Object.freeze({
        matched: true as const,
        result: Object.freeze({
          ok: true as const,
          data: getGovernedSpacetimePeriodsDataset(),
          version,
        }),
        version,
      });
    } catch {
      return matchedFailure(
        "INTEGRITY_FAILURE",
        "the governed Spacetime periods projection failed validation",
        version,
      );
    }
  }

  if (kind === "atlas") {
    if (!allowedQueryOnly(searchParams, new Set(["period"]))) {
      return matchedFailure(
        "INVALID_ARGUMENT",
        "the Spacetime atlas resource accepts only the period query parameter",
        version,
      );
    }
    const periodId = exactlyOne(searchParams, "period");
    if (!periodId) {
      return matchedFailure(
        "INVALID_ARGUMENT",
        "period must be supplied exactly once",
        version,
      );
    }
    const result = lookupGovernedSpacetimeAtlas(periodId);
    return Object.freeze({
      matched: true as const,
      result: result.ok
        ? Object.freeze({ ok: true as const, data: result.data, version })
        : failure(result.code, result.message),
      version,
    });
  }

  if (!allowedQueryOnly(searchParams, new Set(["period", "first", "after"]))) {
    return matchedFailure(
      "INVALID_ARGUMENT",
      "the Spacetime records resource accepts only period, first, and after",
      version,
    );
  }
  const periodId = exactlyOne(searchParams, "period");
  if (!periodId) {
    return matchedFailure(
      "INVALID_ARGUMENT",
      "period must be supplied exactly once",
      version,
    );
  }
  const firstText = optionalOnce(searchParams, "first");
  if (firstText === null || (firstText !== undefined && !/^[1-9][0-9]*$/u.test(firstText))) {
    return matchedFailure(
      "INVALID_ARGUMENT",
      `first must be an integer from 1 through ${MAX_PAGE_SIZE}`,
      version,
    );
  }
  const first = firstText === undefined ? undefined : Number(firstText);
  if (first !== undefined && (!Number.isSafeInteger(first) || first > MAX_PAGE_SIZE)) {
    return matchedFailure(
      "INVALID_ARGUMENT",
      `first must be an integer from 1 through ${MAX_PAGE_SIZE}`,
      version,
    );
  }
  const after = optionalOnce(searchParams, "after");
  if (after === null || (after !== undefined && after.length > MAX_CURSOR_LENGTH)) {
    return matchedFailure(
      "INVALID_ARGUMENT",
      "after must be one non-empty governed cursor",
      version,
    );
  }

  const result = lookupGovernedSpacetimeGeographyRecords(path[5], {
    periodId,
    ...(first === undefined ? {} : { first }),
    ...(after === undefined ? {} : { after }),
  });
  return Object.freeze({
    matched: true as const,
    result: result.ok
      ? Object.freeze({ ok: true as const, data: result.data, version })
      : failure(result.code, result.message),
    version,
  });
}
