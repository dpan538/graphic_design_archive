import type { ArchiveVersionRef, Page, PageRequest, RepoResult } from "./types";

type Cursor = { releaseId: string; manifest: string; resource: string; filter: string; sort: string; key: string };

export function resultError<T>(code: Extract<RepoResult<T>, { ok: false }>['error']['code'], message: string): RepoResult<T> {
  return { ok: false, error: { code, message, retryable: code === "UNAVAILABLE" } };
}

export function requireFirst<T>(page: PageRequest): number | RepoResult<T> {
  const first = page.first ?? 50;
  if (!Number.isInteger(first) || first < 1 || first > 100) return resultError<T>("INVALID_ARGUMENT", "first must be an integer from 1 to 100");
  return first;
}

export function encodeCursor(version: ArchiveVersionRef, resource: string, filter: string, sort: string, key: string): string {
  const value: Cursor = { releaseId: version.research.researchReleaseId, manifest: version.research.researchManifestSha256, resource, filter, sort, key };
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

export function decodeCursor<T>(version: ArchiveVersionRef, page: PageRequest, resource: string, filter: string, sort: string): string | RepoResult<T> | null {
  if (!page.after) return null;
  try {
    const parsed = JSON.parse(Buffer.from(page.after, "base64url").toString("utf8")) as Cursor;
    if (parsed.releaseId !== version.research.researchReleaseId || parsed.manifest !== version.research.researchManifestSha256) return resultError<T>("RELEASE_VERSION_MISMATCH", "cursor belongs to another research release");
    if (parsed.resource !== resource || parsed.filter !== filter || parsed.sort !== sort || !parsed.key) return resultError<T>("INVALID_CURSOR", "cursor does not match this request");
    return parsed.key;
  } catch { return resultError<T>("INVALID_CURSOR", "cursor is malformed"); }
}

export function keysetPage<T>(items: readonly T[], keyFor: (value: T) => string, version: ArchiveVersionRef, request: PageRequest, resource: string, filter: string, sort: string): RepoResult<Page<T>> {
  const first = requireFirst<Page<T>>(request);
  if (typeof first !== "number") return first;
  const after = decodeCursor<Page<T>>(version, request, resource, filter, sort);
  if (after && typeof after !== "string") return after;
  const ordered = [...items].sort((a, b) => keyFor(a).localeCompare(keyFor(b)));
  const start = after ? ordered.findIndex((item) => keyFor(item) === after) + 1 : 0;
  if (after && start === 0) return resultError<Page<T>>("INVALID_CURSOR", "cursor terminal key is unavailable");
  const window = ordered.slice(start, start + first + 1);
  const hasNextPage = window.length > first;
  const nodes = hasNextPage ? window.slice(0, -1) : window;
  const finalKey = nodes.at(-1) ? keyFor(nodes.at(-1)!) : null;
  return { ok: true, version, data: { nodes, pageInfo: { hasNextPage, nextCursor: hasNextPage && finalKey ? encodeCursor(version, resource, filter, sort, finalKey) : null, totalExact: ordered.length } } };
}
