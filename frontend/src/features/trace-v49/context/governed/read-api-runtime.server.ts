import "server-only";

import type { ArchiveVersionRef, RepoResult } from "@/lib/read-platform/types";
import type { PublicContextDataset } from "./types";
import {
  getGovernedContextProjectionInfo,
  lookupGovernedContextDataset,
} from "./reader.server";

export type GovernedContextReadApiMatch =
  | Readonly<{ matched: false }>
  | Readonly<{
    matched: true;
    result: RepoResult<PublicContextDataset>;
    version?: ArchiveVersionRef;
  }>;

const CONTEXT_PATH_TEMPLATE = Object.freeze([
  "releases",
  "{release}",
  "trace",
  "objects",
  "{id}",
  "context",
]);

function isContextResourcePath(path: readonly string[]): boolean {
  return path.length === CONTEXT_PATH_TEMPLATE.length
    && path[0] === "releases"
    && Boolean(path[1])
    && path[2] === "trace"
    && path[3] === "objects"
    && Boolean(path[4])
    && path[5] === "context";
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
      schemaVersion: "archive-research-release/v1",
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
  code: "RELEASE_NOT_FOUND" | "INTEGRITY_FAILURE",
  message: string,
): RepoResult<PublicContextDataset> {
  return Object.freeze({
    ok: false as const,
    error: Object.freeze({ code, message, retryable: false }),
  });
}

/**
 * Resolve the Context resource directly from its committed projection.
 *
 * This branch deliberately runs before the generic repository provider opens,
 * keeping Search and other release adapters outside the normal Context request.
 */
export function tryReadGovernedContextApiResource(
  path: readonly string[],
  requestedManifestSha256: string | null,
): GovernedContextReadApiMatch {
  if (!isContextResourcePath(path)) return Object.freeze({ matched: false as const });

  let info: ReturnType<typeof getGovernedContextProjectionInfo>;
  try {
    info = getGovernedContextProjectionInfo();
  } catch {
    return Object.freeze({
      matched: true as const,
      result: failure(
        "INTEGRITY_FAILURE",
        "the governed Context projection failed validation",
      ),
    });
  }

  const requestedReleaseId = path[1];
  const exactRelease = requestedReleaseId !== "current";
  if (
    exactRelease
    && (
      requestedReleaseId !== info.researchReleaseId
      || requestedManifestSha256 !== info.researchManifestSha256
    )
  ) {
    return Object.freeze({
      matched: true as const,
      result: failure(
        "RELEASE_NOT_FOUND",
        "requested exact research release pair is unavailable",
      ),
    });
  }

  const version = versionFor(info.researchReleaseId, info.researchManifestSha256);
  const lookup = lookupGovernedContextDataset(path[4], {
    researchReleaseId: info.researchReleaseId,
    researchManifestSha256: info.researchManifestSha256,
  });
  if (!lookup.ok) {
    return Object.freeze({
      matched: true as const,
      result: Object.freeze({
        ok: false as const,
        error: Object.freeze({
          code: lookup.code,
          message: lookup.message,
          retryable: false,
        }),
      }),
      version,
    });
  }
  return Object.freeze({
    matched: true as const,
    result: Object.freeze({ ok: true as const, data: lookup.data, version }),
    version,
  });
}
